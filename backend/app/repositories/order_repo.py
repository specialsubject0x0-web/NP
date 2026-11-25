"""訂單、付款、優惠券的資料存取。"""

from sqlalchemy import Select, delete, func, select, update
from sqlalchemy.orm import Session

from app.models import Coupon, CouponRedemption, Order, Payment
from app.repositories._util import affected_one


def get_for_user(db: Session, user_id: int, order_id: int) -> Order | None:
    """只找這位會員自己的訂單（R-13）。"""
    return db.scalar(select(Order).where(Order.id == order_id, Order.user_id == user_id))


def get(db: Session, order_id: int) -> Order | None:
    return db.get(Order, order_id)


def get_by_idempotency(db: Session, user_id: int, key: str) -> Order | None:
    return db.scalar(select(Order).where(Order.user_id == user_id, Order.idempotency_key == key))


def paginate(db: Session, stmt: Select[Order], page: int, page_size: int) -> tuple[list[Order], int]:
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.order_by(Order.created_at.desc(), Order.id.desc()).offset((page - 1) * page_size).limit(page_size))
    return list(rows), total


def user_orders_stmt(user_id: int) -> Select[Order]:
    return select(Order).where(Order.user_id == user_id)


def all_orders_stmt(status: str | None) -> Select[Order]:
    stmt = select(Order)
    return stmt.where(Order.status == status) if status else stmt


def update_status(db: Session, order_id: int, from_status: str, to_status: str) -> bool:
    """改訂單狀態，但只有在「目前狀態仍是 from_status」時才改（避免兩個請求同時改到）。"""
    result = db.execute(
        update(Order)
        .where(Order.id == order_id, Order.status == from_status)
        .values(status=to_status)
        .execution_options(synchronize_session=False)
    )
    return affected_one(result)


def get_payment_by_txn(db: Session, transaction_id: str) -> Payment | None:
    return db.scalar(select(Payment).where(Payment.transaction_id == transaction_id))


def get_payment_by_idempotency(db: Session, order_id: int, key: str) -> Payment | None:
    return db.scalar(select(Payment).where(Payment.order_id == order_id, Payment.idempotency_key == key))


def finish_payment(db: Session, payment_id: int, status: str) -> bool:
    """把 pending 的付款改成最終狀態；已處理過的回傳 False（回呼冪等 R-10）。"""
    result = db.execute(
        update(Payment)
        .where(Payment.id == payment_id, Payment.status == 'pending')
        .values(status=status)
        .execution_options(synchronize_session=False)
    )
    return affected_one(result)


def get_coupon(db: Session, code: str) -> Coupon | None:
    return db.scalar(select(Coupon).where(Coupon.code == code.upper()))


def has_redeemed(db: Session, coupon_id: int, user_id: int) -> bool:
    return (
        db.scalar(select(CouponRedemption.id).where(CouponRedemption.coupon_id == coupon_id, CouponRedemption.user_id == user_id))
        is not None
    )


def claim_coupon(db: Session, coupon_id: int) -> bool:
    """使用次數 +1，但只有在還沒達上限時才加（條件式 UPDATE，同 ADR-003 的道理）。"""
    result = db.execute(
        update(Coupon)
        .where(Coupon.id == coupon_id, (Coupon.usage_limit.is_(None)) | (Coupon.used_count < Coupon.usage_limit))
        .values(used_count=Coupon.used_count + 1)
        .execution_options(synchronize_session=False)
    )
    return affected_one(result)


def release_coupon_for_order(db: Session, order_id: int) -> None:
    """取消訂單時歸還優惠券：刪除使用紀錄、使用次數 -1（R-09）。"""
    redemption = db.scalar(select(CouponRedemption).where(CouponRedemption.order_id == order_id))
    if redemption is None:
        return
    db.execute(
        update(Coupon)
        .where(Coupon.id == redemption.coupon_id, Coupon.used_count > 0)
        .values(used_count=Coupon.used_count - 1)
        .execution_options(synchronize_session=False)
    )
    db.execute(delete(CouponRedemption).where(CouponRedemption.id == redemption.id))
