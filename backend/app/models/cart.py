"""購物車與收件地址的資料表。每一列都屬於某位會員（user_id），查詢時一定要帶 user_id 過濾（防越權 R-13）。"""

from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UTCDateTime, utcnow
from app.models.catalog import Product


class CartItem(Base):
    """購物車中的一項商品。同一會員同一商品只會有一列（用數量表示幾件）。"""

    __tablename__ = 'cart_items'
    __table_args__ = (
        UniqueConstraint('user_id', 'product_id', name='uq_cart_user_product'),
        CheckConstraint('quantity > 0', name='ck_cart_quantity_pos'),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id'))
    quantity: Mapped[int] = mapped_column(Integer)

    product: Mapped[Product] = relationship(lazy='joined')


class Address(Base):
    """收件地址。【重要】姓名、電話、地址屬於個人資料，只能給本人與管理員看，log 中不可印出。"""

    __tablename__ = 'addresses'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    recipient: Mapped[str] = mapped_column(String(50))
    phone: Mapped[str] = mapped_column(String(20))
    postal_code: Mapped[str] = mapped_column(String(6))
    city: Mapped[str] = mapped_column(String(20))
    line: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
