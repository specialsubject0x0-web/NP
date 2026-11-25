"""US-006 模擬付款（R-08、R-10、R-11）。"""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import sign_payment
from app.models import Order, Payment
from tests.conftest import NO_CSRF, place_order

SECRET = 'test-secret'


def pay(c: Any, oid: int, key: str = 'pay-key-0001') -> Any:
    return c.post(f'/api/v1/orders/{oid}/payments', headers={'Idempotency-Key': key})


def test_pay_marks_order_paid(member: Any) -> None:
    oid = place_order(member, {1: 1}).json()['id']
    res = pay(member, oid)
    assert res.status_code == 200
    body = res.json()
    assert body['status'] == 'succeeded' and body['order_status'] == 'paid' and body['transaction_id'].startswith('MOCK-')
    assert member.get(f'/api/v1/orders/{oid}').json()['status'] == 'paid'


def test_pay_is_idempotent(member: Any, db: Session) -> None:
    oid = place_order(member, {1: 1}).json()['id']
    a, b = pay(member, oid), pay(member, oid)
    assert a.json()['transaction_id'] == b.json()['transaction_id']
    assert len(list(db.scalars(select(Payment).where(Payment.order_id == oid)))) == 1
    third = pay(member, oid, key='another-key-01')  # 已付款訂單換 key 再付 → 拒絕
    assert third.status_code == 409


def test_cannot_pay_cancelled_or_others_order(member: Any, other_member: Any) -> None:
    oid = place_order(member, {1: 1}).json()['id']
    assert pay(other_member, oid).status_code == 404
    member.post(f'/api/v1/orders/{oid}/cancel')
    assert pay(member, oid).status_code == 409
    assert pay(member, oid, key='x').status_code == 400  # Key 太短


def _pending_payment(db: Session, member: Any) -> Payment:
    oid = place_order(member, {1: 1}).json()['id']
    payment = Payment(order_id=oid, transaction_id='EXT-0001', amount=680 + 60, status='pending', idempotency_key='ext-key-0001')
    db.add(payment)
    db.commit()
    return payment


def callback(c: Any, payment: Payment, *, amount: int | None = None, status: str = 'succeeded', signature: str | None = None) -> Any:
    amt = payment.amount if amount is None else amount
    sig = signature if signature is not None else sign_payment(SECRET, payment.transaction_id, payment.order_id, amt, status)
    body = {'transaction_id': payment.transaction_id, 'order_id': payment.order_id, 'amount': amt, 'status': status}
    return c.post('/api/v1/payments/callback', json=body, headers={'X-Signature': sig, NO_CSRF: '1'})


def test_callback_bad_signature_rejected(client: Any, member: Any, db: Session) -> None:
    payment = _pending_payment(db, member)
    res = callback(client, payment, signature='0' * 64)
    assert res.status_code == 400 and res.json()['code'] == 'PAYMENT_BAD_SIGNATURE'
    res = client.post(
        '/api/v1/payments/callback',
        json={'transaction_id': 'EXT-0001', 'order_id': 1, 'amount': 1, 'status': 'succeeded'},
        headers={NO_CSRF: '1'},
    )
    assert res.status_code == 400
    db.expire_all()
    assert db.get(Order, payment.order_id).status == 'pending_payment'  # type: ignore[union-attr]


def test_callback_duplicate_processed_once(client: Any, member: Any, db: Session) -> None:
    payment = _pending_payment(db, member)
    assert callback(client, payment).json() == {'received': True, 'payment_status': 'succeeded'}
    assert callback(client, payment).json() == {'received': True, 'payment_status': 'succeeded'}
    db.expire_all()
    assert db.get(Order, payment.order_id).status == 'paid'  # type: ignore[union-attr]


def test_callback_amount_tampered(client: Any, member: Any, db: Session) -> None:
    payment = _pending_payment(db, member)
    res = callback(client, payment, amount=1)  # 簽章正確但金額不同
    assert res.status_code == 400 and res.json()['code'] == 'PAYMENT_MISMATCH'


def test_callback_unknown_transaction(client: Any) -> None:
    fake = Payment(order_id=1, transaction_id='NOPE', amount=1, status='pending', idempotency_key='k')
    assert callback(client, fake).status_code == 404


def test_callback_failed_status(client: Any, member: Any, db: Session) -> None:
    payment = _pending_payment(db, member)
    assert callback(client, payment, status='failed').json()['payment_status'] == 'failed'
    db.expire_all()
    assert db.get(Order, payment.order_id).status == 'pending_payment'  # type: ignore[union-attr]


def test_callback_after_cancel_marks_payment_failed(client: Any, member: Any, db: Session) -> None:
    payment = _pending_payment(db, member)
    member.post(f'/api/v1/orders/{payment.order_id}/cancel')
    assert callback(client, payment).json()['payment_status'] == 'failed'
    db.expire_all()
    assert db.get(Order, payment.order_id).status == 'cancelled'  # type: ignore[union-attr]
