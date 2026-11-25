"""訂單、訂單明細、付款紀錄的資料表。

【重要】訂單明細保存「下單當下」的商品名稱與單價（價格快照 R-07），所以不用關聯回商品表去拿價格。
【重要】付款只存交易編號與狀態，絕不存信用卡號（R-10）。
"""

from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UTCDateTime, utcnow

# 訂單狀態（R-08）。狀態之間能怎麼轉換，定義在 app/services/order_state.py
ORDER_STATUSES = ('pending_payment', 'paid', 'shipped', 'completed', 'cancelled')


class Order(Base):
    """一筆訂單。金額欄位都是整數元，由後端計算（前端算的只供顯示）。"""

    __tablename__ = 'orders'
    __table_args__ = (UniqueConstraint('user_id', 'idempotency_key', name='uq_orders_user_idem'),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    status: Mapped[str] = mapped_column(String(20), default='pending_payment', index=True)
    subtotal: Mapped[int] = mapped_column(Integer)
    discount: Mapped[int] = mapped_column(Integer, default=0)
    shipping_fee: Mapped[int] = mapped_column(Integer)
    total: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3), default='TWD')
    coupon_code: Mapped[str | None] = mapped_column(String(32), default=None)
    # 【為什麼】Idempotency-Key（冪等鍵）：前端每次「送出訂單」產生一個隨機字串；按兩次也只會建立一筆
    idempotency_key: Mapped[str] = mapped_column(String(64))
    # 收件資訊快照：之後會員改地址，不會影響已成立的訂單
    recipient_name: Mapped[str] = mapped_column(String(50))
    recipient_phone: Mapped[str] = mapped_column(String(20))
    shipping_address: Mapped[str] = mapped_column(String(240))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, onupdate=utcnow)

    items: Mapped[list[OrderItem]] = relationship(back_populates='order', lazy='selectin', cascade='all, delete-orphan')


class OrderItem(Base):
    """訂單中的一項商品（價格快照）。"""

    __tablename__ = 'order_items'

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey('orders.id', ondelete='CASCADE'), index=True)
    product_id: Mapped[int] = mapped_column(Integer)  # 只記編號，不設外鍵：商品之後怎麼改都不影響訂單
    product_name: Mapped[str] = mapped_column(String(100))
    unit_price: Mapped[int] = mapped_column(Integer)
    quantity: Mapped[int] = mapped_column(Integer)
    line_total: Mapped[int] = mapped_column(Integer)

    order: Mapped[Order] = relationship(back_populates='items')


class Payment(Base):
    """一次付款嘗試。status：pending（等待金流）、succeeded（成功）、failed（失敗）。"""

    __tablename__ = 'payments'
    __table_args__ = (UniqueConstraint('order_id', 'idempotency_key', name='uq_payments_order_idem'),)

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey('orders.id'), index=True)
    transaction_id: Mapped[str] = mapped_column(String(64), unique=True)
    amount: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default='pending')
    idempotency_key: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
