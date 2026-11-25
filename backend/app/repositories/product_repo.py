"""商品的資料存取。

【重要】所有查詢都用 SQLAlchemy 組條件（參數化），絕不把使用者輸入直接拼進 SQL 字串（防 SQL 注入）。
"""

from typing import Any

from sqlalchemy import Select, UnaryExpression, func, or_, select, update
from sqlalchemy.orm import Session

from app.models import Category, Product
from app.repositories._util import affected_one
from app.schemas.product import ProductQuery

# 排序白名單（R-18）：使用者只能選這幾種，對應到固定的欄位
_SORTS: dict[str, tuple[UnaryExpression[Any], UnaryExpression[Any]]] = {
    'newest': (Product.created_at.desc(), Product.id.desc()),
    'price_asc': (Product.price.asc(), Product.id.asc()),
    'price_desc': (Product.price.desc(), Product.id.asc()),
    'name': (Product.name.asc(), Product.id.asc()),
}


def _escape_like(text: str) -> str:
    """把 % 和 _ 當成一般字元搜尋（否則使用者輸入 % 會變成「全部符合」）。"""
    return text.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')


def search(db: Session, query: ProductQuery, *, include_inactive: bool = False) -> tuple[list[Product], int]:
    """依條件搜尋商品，回傳（這一頁的商品, 全部筆數）。"""
    stmt: Select[Product] = select(Product)
    if not include_inactive:
        stmt = stmt.where(Product.is_active.is_(True))
    if query.q:
        pattern = f'%{_escape_like(query.q)}%'
        stmt = stmt.where(or_(Product.name.ilike(pattern, escape='\\'), Product.description.ilike(pattern, escape='\\')))
    if query.category_id is not None:
        stmt = stmt.where(Product.category_id == query.category_id)
    if query.min_price is not None:
        stmt = stmt.where(Product.price >= query.min_price)
    if query.max_price is not None:
        stmt = stmt.where(Product.price <= query.max_price)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    stmt = stmt.order_by(*_SORTS[query.sort]).offset((query.page - 1) * query.page_size).limit(query.page_size)
    return list(db.scalars(stmt).unique()), total


def get(db: Session, product_id: int) -> Product | None:
    return db.get(Product, product_id)


def list_categories(db: Session) -> list[Category]:
    return list(db.scalars(select(Category).order_by(Category.id)))


def category_exists(db: Session, category_id: int) -> bool:
    return db.get(Category, category_id) is not None


def decrement_stock(db: Session, product_id: int, quantity: int) -> bool:
    """扣庫存。回傳 True 代表成功；False 代表庫存不足或商品已下架。

    【重要】【為什麼】用「條件式 UPDATE」一次完成「檢查庫存＋扣除」：
    兩個人同時買最後一件時，資料庫保證只有一個人的 UPDATE 會成功（另一個影響 0 列），不會超賣（ADR-003）。
    千萬不要改成「先 SELECT 庫存，再用 Python 判斷後 UPDATE」，那樣兩人會同時看到「還有 1 件」。
    """
    result = db.execute(
        update(Product)
        .where(Product.id == product_id, Product.is_active.is_(True), Product.stock >= quantity)
        .values(stock=Product.stock - quantity)
        .execution_options(synchronize_session=False)
    )
    return affected_one(result)


def increment_stock(db: Session, product_id: int, quantity: int) -> None:
    """回補庫存（取消訂單時使用）。"""
    db.execute(
        update(Product).where(Product.id == product_id).values(stock=Product.stock + quantity).execution_options(synchronize_session=False)
    )
