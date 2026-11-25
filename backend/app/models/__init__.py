"""資料表（由 dba 負責）。匯入這個套件就會註冊所有資料表，Alembic 產生 Migration 時需要。"""

from app.models.base import Base
from app.models.cart import Address, CartItem
from app.models.catalog import Category, Product
from app.models.coupon import Coupon, CouponRedemption
from app.models.order import Order, OrderItem, Payment
from app.models.user import User, UserSession

__all__ = [
    'Address',
    'Base',
    'CartItem',
    'Category',
    'Coupon',
    'CouponRedemption',
    'Order',
    'OrderItem',
    'Payment',
    'Product',
    'User',
    'UserSession',
]
