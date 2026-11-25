"""模擬金流與付款回呼（US-006、ADR-004）。

流程：
  會員按「付款」→ start_payment 建立一筆付款（交易編號）
  → 模擬金流 _mock_gateway 產生「已簽章」的回呼內容
  → handle_callback 驗證簽章、確認金額、把訂單改成 paid
未來換成真的金流時，只要把 _mock_gateway 換掉；handle_callback 的檢查邏輯不變。
【重要】這裡不收、不存、不記錄任何信用卡資料（R-10）。
"""

import secrets

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.security import sign_payment, tokens_equal
from app.models import Order, Payment, User
from app.repositories import order_repo
from app.schemas.order import PaymentCallbackIn
from app.services import order_service, order_state


def start_payment(db: Session, user: User, order_id: int, idempotency_key: str) -> tuple[Payment, Order]:
    """對自己的待付款訂單付款。同一個 Idempotency-Key 重送 → 回傳同一筆付款（R-11）。"""
    order = order_service.get_user_order(db, user, order_id)
    existing = order_repo.get_payment_by_idempotency(db, order.id, idempotency_key)
    if existing is not None:
        db.refresh(order)
        return existing, order
    order_state.ensure_transition(order.status, 'paid')

    payment = Payment(
        order_id=order.id,
        transaction_id=f'MOCK-{secrets.token_hex(8).upper()}',
        amount=order.total,
        status='pending',
        idempotency_key=idempotency_key,
    )
    db.add(payment)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = order_repo.get_payment_by_idempotency(db, order.id, idempotency_key)
        if existing is None:  # pragma: no cover - 理論上不會發生
            raise
        return existing, order
    _mock_gateway(db, payment)
    db.refresh(payment)
    db.refresh(order)
    return payment, order


def _mock_gateway(db: Session, payment: Payment) -> None:
    """模擬金流：一律付款成功，並用金鑰簽章後送回呼（真金流會從外部打 /payments/callback）。"""
    secret = get_settings().payment_webhook_secret
    status = 'succeeded'
    signature = sign_payment(secret, payment.transaction_id, payment.order_id, payment.amount, status)
    data = PaymentCallbackIn(transaction_id=payment.transaction_id, order_id=payment.order_id, amount=payment.amount, status=status)
    handle_callback(db, data, signature)


def handle_callback(db: Session, data: PaymentCallbackIn, signature: str | None) -> Payment:
    """處理金流回呼。

    1. 驗證簽章：不對就拒絕（400），訂單完全不動（R-10）
    2. 找付款紀錄，確認訂單編號與金額一致（防止竄改金額）
    3. 冪等：已處理過的交易直接回傳，不重複處理
    """
    expected = sign_payment(get_settings().payment_webhook_secret, data.transaction_id, data.order_id, data.amount, data.status)
    if not tokens_equal(signature, expected):
        raise AppError(400, 'PAYMENT_BAD_SIGNATURE', '付款通知驗證失敗')

    payment = order_repo.get_payment_by_txn(db, data.transaction_id)
    if payment is None:
        raise AppError(404, 'PAYMENT_NOT_FOUND', '找不到這筆付款')
    if payment.order_id != data.order_id or payment.amount != data.amount:
        raise AppError(400, 'PAYMENT_MISMATCH', '付款資料不一致')
    if payment.status != 'pending':
        return payment  # 重複回呼：已經處理過，什麼都不做

    order = order_repo.get(db, payment.order_id)
    if order is None:  # pragma: no cover - 外鍵保證存在
        raise AppError(404, 'ORDER_NOT_FOUND', '找不到這筆訂單')

    final_status = data.status
    if final_status == 'succeeded' and not order_state.can_transition(order.status, 'paid'):
        # 例如：付款途中訂單被取消。付款標記失敗，訂單狀態不變（實務上需人工退款，見假設 A-05）
        final_status = 'failed'
    if not order_repo.finish_payment(db, payment.id, final_status):
        db.rollback()
        db.refresh(payment)
        return payment  # 同時有另一個回呼先處理完了
    if final_status == 'succeeded':
        order_repo.update_status(db, order.id, 'pending_payment', 'paid')
    db.commit()
    db.refresh(payment)
    return payment
