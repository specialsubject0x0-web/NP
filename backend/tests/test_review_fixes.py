"""審查發現的 Bug 重現測試（AGENTS.md：每個 Bug 先寫重現測試再修）。見 docs/reviews/sprint-1-review.md。"""

import threading
from typing import Any

from sqlalchemy.orm import Session, sessionmaker

from app.core import rate_limit
from app.core.config import get_settings
from app.core.errors import AppError
from app.core.security import sign_payment
from app.models import Order, Payment, User
from app.schemas.auth import LoginIn
from app.schemas.order import PaymentCallbackIn
from app.services import auth_service, payment_service
from tests.conftest import DEMO, place_order


def _callback(db: Session, payment: Payment) -> Payment:
    sig = sign_payment(get_settings().payment_webhook_secret, payment.transaction_id, payment.order_id, payment.amount, 'succeeded')
    data = PaymentCallbackIn(transaction_id=payment.transaction_id, order_id=payment.order_id, amount=payment.amount, status='succeeded')
    return payment_service.handle_callback(db, data, sig)


def test_bug1_payment_on_order_cancelled_by_another_request(member: Any, session_factory: sessionmaker[Session]) -> None:
    """付款回呼用的是「快取中的舊訂單」：另一個請求已取消訂單，付款卻仍標成成功。"""
    oid = place_order(member, {1: 1}).json()['id']
    with session_factory() as a:
        payment = Payment(order_id=oid, transaction_id='RACE-1', amount=740, status='pending', idempotency_key='race-key-1')
        a.add(payment)
        a.commit()
        # 【為什麼】要留著這個參考：真實程式 start_payment 也握著訂單物件，Session 才會一直用快取裡的舊狀態
        cached = a.get(Order, oid)
        assert cached is not None and cached.status == 'pending_payment'
        assert member.post(f'/api/v1/orders/{oid}/cancel').status_code == 200  # 另一個請求取消了訂單
        result = _callback(a, payment)
    with session_factory() as check:
        assert check.get(Order, oid).status == 'cancelled'  # type: ignore[union-attr]
        assert result.status == 'failed'  # 不可以對已取消的訂單收款
        del cached


def test_bug1_two_payments_only_one_succeeds(member: Any, session_factory: sessionmaker[Session]) -> None:
    """同一筆訂單兩筆付款（兩個分頁、不同 key），只能有一筆成功，不可重複扣款。"""
    oid = place_order(member, {1: 1}).json()['id']
    with session_factory() as a, session_factory() as b:
        p1 = Payment(order_id=oid, transaction_id='DUP-1', amount=740, status='pending', idempotency_key='dup-key-1')
        p2 = Payment(order_id=oid, transaction_id='DUP-2', amount=740, status='pending', idempotency_key='dup-key-2')
        a.add_all([p1, p2])
        a.commit()
        cached_b = a.get(Order, oid), b.get(Order, oid)  # 兩個 Session 都握著「待付款」的舊物件
        r1 = _callback(a, p1)
        r2 = _callback(b, b.get(Payment, p2.id))  # type: ignore[arg-type]
    assert sorted([r1.status, r2.status]) == ['failed', 'succeeded']
    assert all(o is not None for o in cached_b)


def test_bug2_login_rate_limit_not_bypassed_by_concurrency(session_factory: sessionmaker[Session]) -> None:
    """同時送出大量錯誤密碼：最多只能真的驗證 5 次，其餘都要被 429 擋下（R-15）。"""
    rate_limit.reset_all()
    outcomes: list[int] = []
    lock = threading.Lock()
    barrier = threading.Barrier(20)

    def attempt() -> None:
        with session_factory() as db:
            barrier.wait()
            try:
                auth_service.login(db, LoginIn(email=DEMO[0], password='wrong-password'), '1.2.3.4')
                code = 200
            except AppError as exc:
                code = exc.status_code
            with lock:
                outcomes.append(code)

    threads = [threading.Thread(target=attempt) for _ in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert outcomes.count(401) <= 5
    assert outcomes.count(429) >= 15
    with session_factory() as db:
        assert db.query(User).count() == 2
