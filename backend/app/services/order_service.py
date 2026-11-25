"""建立訂單、查詢訂單、取消訂單（US-005、US-007、US-010）。

最重要的函式是 create_order：
1. 同一個 Idempotency-Key 已經下過單 → 直接回傳舊訂單（R-11）
2. 用 pricing_service 重新計算金額（不相信前端）
3. 在「同一個交易」裡：扣庫存 → 建立訂單與明細 → 使用優惠券 → 清空購物車（R-06）
   任何一步失敗就 rollback（全部還原），不會出現「扣了庫存卻沒有訂單」。
"""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models import CouponRedemption, Order, OrderItem, User
from app.repositories import cart_repo, order_repo, product_repo
from app.services import order_state, pricing_service


def create_order(db: Session, user: User, address_id: int, coupon_code: str | None, idempotency_key: str) -> tuple[Order, bool]:
    """建立訂單。回傳（訂單, 是否為新建立）。重複請求回傳 (舊訂單, False)。"""
    existing = order_repo.get_by_idempotency(db, user.id, idempotency_key)
    if existing is not None:
        return existing, False

    address = cart_repo.get_address(db, user.id, address_id)
    if address is None:
        raise AppError(404, 'ADDRESS_NOT_FOUND', '找不到這個地址')

    quote = pricing_service.build_quote(db, user, coupon_code)
    try:
        # 【重要】扣庫存與建立訂單在同一個交易（R-06），任何商品不夠就整筆取消
        for line in quote.lines:
            if not product_repo.decrement_stock(db, line.product_id, line.quantity):
                raise AppError(409, 'ORDER_OUT_OF_STOCK', f'「{line.name}」庫存不足', {'product_id': line.product_id})

        order = Order(
            user_id=user.id,
            status='pending_payment',
            subtotal=quote.subtotal,
            discount=quote.discount,
            shipping_fee=quote.shipping_fee,
            total=quote.total,
            currency=quote.currency,
            coupon_code=quote.coupon_code,
            idempotency_key=idempotency_key,
            recipient_name=address.recipient,
            recipient_phone=address.phone,
            shipping_address=f'{address.postal_code} {address.city}{address.line}',
            # 價格快照（R-07）：把當下的名稱與單價抄進訂單明細
            items=[
                OrderItem(
                    product_id=line.product_id,
                    product_name=line.name,
                    unit_price=line.unit_price,
                    quantity=line.quantity,
                    line_total=line.line_total,
                )
                for line in quote.lines
            ],
        )
        db.add(order)
        db.flush()  # 先拿到訂單編號

        if quote.coupon is not None:
            if not order_repo.claim_coupon(db, quote.coupon.id):
                raise AppError(409, 'COUPON_USAGE_LIMIT_REACHED', '這張優惠券已經被用完了')
            db.add(CouponRedemption(coupon_id=quote.coupon.id, user_id=user.id, order_id=order.id))
            db.flush()

        cart_repo.clear(db, user.id)
        db.commit()
    except AppError:
        db.rollback()
        raise
    except IntegrityError:
        # 兩種可能：同一個 Idempotency-Key 同時送了兩次，或同一張券同時被同一人使用
        db.rollback()
        existing = order_repo.get_by_idempotency(db, user.id, idempotency_key)
        if existing is not None:
            return existing, False
        raise AppError(409, 'COUPON_ALREADY_USED', '你已經用過這張優惠券了') from None
    db.refresh(order)
    return order, True


def get_user_order(db: Session, user: User, order_id: int) -> Order:
    """查自己的訂單；別人的訂單回 404（R-13）。"""
    order = order_repo.get_for_user(db, user.id, order_id)
    if order is None:
        raise AppError(404, 'ORDER_NOT_FOUND', '找不到這筆訂單')
    return order


def list_user_orders(db: Session, user: User, page: int, page_size: int) -> tuple[list[Order], int]:
    return order_repo.paginate(db, order_repo.user_orders_stmt(user.id), page, page_size)


def transition(db: Session, order: Order, target: str) -> Order:
    """依狀態機改變訂單狀態；取消時回補庫存並歸還優惠券（R-09）。"""
    order_state.ensure_transition(order.status, target)
    if not order_repo.update_status(db, order.id, order.status, target):
        # 有另一個請求剛好先改了狀態
        db.rollback()
        raise AppError(409, 'ORDER_INVALID_TRANSITION', '訂單狀態已經改變，請重新整理')
    if target == 'cancelled':
        for item in order.items:
            product_repo.increment_stock(db, item.product_id, item.quantity)
        order_repo.release_coupon_for_order(db, order.id)
    db.commit()
    db.refresh(order)
    return order


def cancel_by_user(db: Session, user: User, order_id: int) -> Order:
    return transition(db, get_user_order(db, user, order_id), 'cancelled')
