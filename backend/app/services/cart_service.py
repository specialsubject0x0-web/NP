"""購物車與地址的商業規則（US-003、US-004）。

【重要】購物車的小計只是「給使用者看的參考」；真正的金額在結帳時由 pricing_service 重新計算。
"""

from sqlalchemy.orm import Session

from app.core import business_rules as rules
from app.core.errors import AppError
from app.models import Address, CartItem, User
from app.repositories import cart_repo, product_repo
from app.schemas.cart import AddressIn, CartItemOut, CartOut


def _to_out(items: list[CartItem]) -> CartOut:
    lines = [
        CartItemOut(
            product_id=i.product_id,
            name=i.product.name,
            unit_price=i.product.price,
            quantity=i.quantity,
            line_total=i.product.price * i.quantity,
            stock=i.product.stock,
            image_color=i.product.image_color,
            is_available=i.product.is_active and i.product.stock >= i.quantity,
        )
        for i in items
    ]
    return CartOut(
        items=lines,
        item_count=sum(line.quantity for line in lines),
        subtotal=sum(line.line_total for line in lines),
        currency=rules.CURRENCY,
    )


def get_cart(db: Session, user: User) -> CartOut:
    return _to_out(cart_repo.list_items(db, user.id))


def set_quantity(db: Session, user: User, product_id: int, quantity: int) -> CartOut:
    """把某商品的數量設定為 quantity（不是「加上」）。超過庫存 → 409（R-05）。"""
    product = product_repo.get(db, product_id)
    if product is None or not product.is_active:
        raise AppError(404, 'PRODUCT_NOT_FOUND', '找不到這個商品')
    if quantity > product.stock:
        raise AppError(409, 'CART_EXCEEDS_STOCK', f'庫存只剩 {product.stock} 件', {'stock': product.stock})
    item = cart_repo.get_item(db, user.id, product_id)
    if item is None:
        db.add(CartItem(user_id=user.id, product_id=product_id, quantity=quantity))
    else:
        item.quantity = quantity
    db.commit()
    return get_cart(db, user)


def remove_item(db: Session, user: User, product_id: int) -> CartOut:
    cart_repo.remove_item(db, user.id, product_id)
    db.commit()
    return get_cart(db, user)


def list_addresses(db: Session, user: User) -> list[Address]:
    return cart_repo.list_addresses(db, user.id)


def add_address(db: Session, user: User, data: AddressIn) -> Address:
    address = Address(user_id=user.id, **data.model_dump())
    db.add(address)
    db.commit()
    return address


def delete_address(db: Session, user: User, address_id: int) -> None:
    """刪除自己的地址；別人的地址回 404（不透露是否存在，R-13）。"""
    address = cart_repo.get_address(db, user.id, address_id)
    if address is None:
        raise AppError(404, 'ADDRESS_NOT_FOUND', '找不到這個地址')
    db.delete(address)
    db.commit()
