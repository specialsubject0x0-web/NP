"""商品 API：/api/v1/products、/api/v1/categories（US-001、US-002）。不需登入。"""

from typing import Annotated

from fastapi import APIRouter, Path, Query

from app.core.deps import DB
from app.schemas.common import ErrorResponse, Page
from app.schemas.product import CategoryOut, ProductOut, ProductQuery
from app.services import catalog_service

router = APIRouter(tags=['products'])
ProductId = Annotated[int, Path(gt=0, le=2_147_483_647)]


@router.get('/categories', response_model=list[CategoryOut], summary='分類列表')
def list_categories(db: DB) -> list[CategoryOut]:
    return [CategoryOut.model_validate(c) for c in catalog_service.list_categories(db)]


@router.get('/products', response_model=Page[ProductOut], responses={422: {'model': ErrorResponse}}, summary='搜尋商品')
def list_products(query: Annotated[ProductQuery, Query()], db: DB) -> Page[ProductOut]:
    items, total = catalog_service.search_products(db, query)
    return Page[ProductOut](items=[ProductOut.model_validate(p) for p in items], total=total, page=query.page, page_size=query.page_size)


@router.get('/products/{product_id}', response_model=ProductOut, responses={404: {'model': ErrorResponse}}, summary='商品詳情')
def get_product(product_id: ProductId, db: DB) -> ProductOut:
    return ProductOut.model_validate(catalog_service.get_product(db, product_id))
