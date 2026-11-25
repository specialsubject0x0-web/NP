"""購物車與地址的資料存取。【重要】每個查詢都帶 user_id 條件，確保只拿得到自己的資料（R-13）。"""

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import Address, CartItem


def list_items(db: Session, user_id: int) -> list[CartItem]:
    return list(db.scalars(select(CartItem).where(CartItem.user_id == user_id).order_by(CartItem.id)).unique())


def get_item(db: Session, user_id: int, product_id: int) -> CartItem | None:
    return db.scalar(select(CartItem).where(CartItem.user_id == user_id, CartItem.product_id == product_id))


def remove_item(db: Session, user_id: int, product_id: int) -> None:
    db.execute(delete(CartItem).where(CartItem.user_id == user_id, CartItem.product_id == product_id))


def clear(db: Session, user_id: int) -> None:
    db.execute(delete(CartItem).where(CartItem.user_id == user_id))


def list_addresses(db: Session, user_id: int) -> list[Address]:
    return list(db.scalars(select(Address).where(Address.user_id == user_id).order_by(Address.id)))


def get_address(db: Session, user_id: int, address_id: int) -> Address | None:
    """只找「這位會員自己的」地址；別人的地址一律當作不存在。"""
    return db.scalar(select(Address).where(Address.id == address_id, Address.user_id == user_id))
