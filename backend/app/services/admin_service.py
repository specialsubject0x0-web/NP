"""後台管理的商業規則（US-009、US-010）。只有 admin 能呼叫（權限在 routers/admin.py 用 require_admin 檢查）。"""

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models import Order, Product
from app.repositories import order_repo, product_repo
from app.schemas.product import ProductCreateIn, ProductQuery, ProductUpdateIn
from app.services import order_service


def list_products(db: Session, query: ProductQuery) -> tuple[list[Product], int]:
    return product_repo.search(db, query, include_inactive=True)


def _check_category(db: Session, category_id: int | None) -> None:
    if category_id is not None and not product_repo.category_exists(db, category_id):
        raise AppError(422, 'CATEGORY_NOT_FOUND', '分類不存在')


def create_product(db: Session, data: ProductCreateIn) -> Product:
    _check_category(db, data.category_id)
    product = Product(**data.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def update_product(db: Session, product_id: int, data: ProductUpdateIn) -> Product:
    """只更新有送來的欄位。改價只影響之後的新訂單（舊訂單有價格快照，R-07）。"""
    product = product_repo.get(db, product_id)
    if product is None:
        raise AppError(404, 'PRODUCT_NOT_FOUND', '找不到這個商品')
    changes = data.model_dump(exclude_unset=True)
    if any(changes.get(k) is None for k in changes):
        raise AppError(422, 'VALIDATION_ERROR', '欄位不可設為空值')
    _check_category(db, changes.get('category_id'))
    for key, value in changes.items():
        setattr(product, key, value)
    db.commit()
    db.refresh(product)
    return product


def list_orders(db: Session, status: str | None, page: int, page_size: int) -> tuple[list[Order], int]:
    return order_repo.paginate(db, order_repo.all_orders_stmt(status), page, page_size)


def get_order(db: Session, order_id: int) -> Order:
    order = order_repo.get(db, order_id)
    if order is None:
        raise AppError(404, 'ORDER_NOT_FOUND', '找不到這筆訂單')
    return order


def transition_order(db: Session, order_id: int, target: str) -> Order:
    return order_service.transition(db, get_order(db, order_id), target)
