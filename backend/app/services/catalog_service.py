"""商品瀏覽的商業規則（US-001、US-002）：前台只看得到上架商品。"""

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models import Category, Product
from app.repositories import product_repo
from app.schemas.product import ProductQuery


def search_products(db: Session, query: ProductQuery) -> tuple[list[Product], int]:
    if query.min_price is not None and query.max_price is not None and query.min_price > query.max_price:
        raise AppError(422, 'INVALID_PRICE_RANGE', '最低價格不能高於最高價格')
    return product_repo.search(db, query)


def get_product(db: Session, product_id: int) -> Product:
    """取得上架中的商品；不存在或已下架都回 404。"""
    product = product_repo.get(db, product_id)
    if product is None or not product.is_active:
        raise AppError(404, 'PRODUCT_NOT_FOUND', '找不到這個商品')
    return product


def list_categories(db: Session) -> list[Category]:
    return product_repo.list_categories(db)
