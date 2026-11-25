"""商品與分類的資料表。

【重要】price 是整數「元」（R-01），禁止改成 float（浮點數會有 0.1+0.2≠0.3 的誤差）。
stock 有資料庫檢查條件 stock >= 0，就算程式有 bug，資料庫也不允許庫存變負數。
"""

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UTCDateTime, utcnow


class Category(Base):
    """商品分類，例如「廚房」「文具」。slug 是網址用的英文代號。"""

    __tablename__ = 'categories'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    slug: Mapped[str] = mapped_column(String(50), unique=True)


class Product(Base):
    """商品。is_active=False 代表下架（不刪除，避免舊訂單找不到商品）。"""

    __tablename__ = 'products'
    __table_args__ = (
        CheckConstraint('price >= 0', name='ck_products_price_nonneg'),
        CheckConstraint('stock >= 0', name='ck_products_stock_nonneg'),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), index=True)
    description: Mapped[str] = mapped_column(Text, default='')
    price: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3), default='TWD')
    stock: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    # 商品圖是前端依這個顏色畫出的佔位圖（沒有授權圖片，假設 A-11）
    image_color: Mapped[str] = mapped_column(String(7), default='#94a3b8')
    category_id: Mapped[int] = mapped_column(ForeignKey('categories.id'), index=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, onupdate=utcnow)

    category: Mapped[Category] = relationship(lazy='joined')
