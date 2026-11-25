"""優惠券與使用紀錄的資料表（R-12）。

kind：fixed = 折固定金額（value 元）；percent = 打折（value 是折扣百分比，例如 10 代表打 9 折）。
【重要】used_count 有檢查條件不可超過 usage_limit；同一會員同一張券只能有一筆使用紀錄（唯一限制）。
"""

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UTCDateTime


class Coupon(Base):
    """優惠券。usage_limit 為 None 代表不限總次數。"""

    __tablename__ = 'coupons'
    __table_args__ = (
        CheckConstraint("kind IN ('fixed', 'percent')", name='ck_coupons_kind'),
        CheckConstraint('value > 0', name='ck_coupons_value_pos'),
        CheckConstraint('usage_limit IS NULL OR used_count <= usage_limit', name='ck_coupons_usage'),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)  # 一律存大寫
    kind: Mapped[str] = mapped_column(String(10))
    value: Mapped[int] = mapped_column(Integer)
    max_discount: Mapped[int | None] = mapped_column(Integer, default=None)
    min_spend: Mapped[int] = mapped_column(Integer, default=0)
    starts_at: Mapped[datetime] = mapped_column(UTCDateTime)
    ends_at: Mapped[datetime] = mapped_column(UTCDateTime)
    usage_limit: Mapped[int | None] = mapped_column(Integer, default=None)
    used_count: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class CouponRedemption(Base):
    """某位會員在某筆訂單用了某張券。唯一限制 (coupon_id, user_id) 保證每人每張只能用一次。"""

    __tablename__ = 'coupon_redemptions'
    __table_args__ = (UniqueConstraint('coupon_id', 'user_id', name='uq_redemption_coupon_user'),)

    id: Mapped[int] = mapped_column(primary_key=True)
    coupon_id: Mapped[int] = mapped_column(ForeignKey('coupons.id'), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey('orders.id', ondelete='CASCADE'), unique=True)
