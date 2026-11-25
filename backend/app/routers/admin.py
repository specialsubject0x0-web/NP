"""後台 API：/api/v1/admin/...（US-009、US-010）。【重要】整個 router 都要求管理員權限（R-14）。"""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from app.core import business_rules as rules
from app.core.deps import DB, require_admin
from app.schemas.common import ErrorResponse, Page
from app.schemas.order import AdminOrderOut, OrderOut, OrderStatus, TransitionIn
from app.schemas.product import AdminProductOut, ProductCreateIn, ProductQuery, ProductUpdateIn
from app.services import admin_service

router = APIRouter(
    prefix='/admin',
    tags=['admin'],
    dependencies=[Depends(require_admin)],
    responses={s: {'model': ErrorResponse} for s in (401, 403, 404, 409, 422)},
)
IdPath = Annotated[int, Path(gt=0, le=2_147_483_647)]


@router.get('/products', response_model=Page[AdminProductOut], summary='商品列表（含下架）')
def list_products(query: Annotated[ProductQuery, Query()], db: DB) -> Page[AdminProductOut]:
    items, total = admin_service.list_products(db, query)
    return Page[AdminProductOut](
        items=[AdminProductOut.model_validate(p) for p in items], total=total, page=query.page, page_size=query.page_size
    )


@router.post('/products', response_model=AdminProductOut, status_code=201, summary='新增商品')
def create_product(data: ProductCreateIn, db: DB) -> AdminProductOut:
    return AdminProductOut.model_validate(admin_service.create_product(db, data))


@router.patch('/products/{product_id}', response_model=AdminProductOut, summary='修改商品（價格、庫存、上下架）')
def update_product(product_id: IdPath, data: ProductUpdateIn, db: DB) -> AdminProductOut:
    return AdminProductOut.model_validate(admin_service.update_product(db, product_id, data))


@router.get('/orders', response_model=Page[AdminOrderOut], summary='全部訂單')
def list_orders(
    db: DB,
    status: Annotated[OrderStatus | None, Query()] = None,
    page: Annotated[int, Query(ge=1, le=10_000)] = 1,
    page_size: Annotated[int, Query(ge=1, le=rules.PAGE_SIZE_MAX)] = 20,
) -> Page[AdminOrderOut]:
    items, total = admin_service.list_orders(db, status, page, page_size)
    out = [
        AdminOrderOut(
            id=o.id,
            status=o.status,
            total=o.total,
            currency=o.currency,
            created_at=o.created_at,
            item_count=sum(i.quantity for i in o.items),
            user_id=o.user_id,
            recipient_name=o.recipient_name,
        )
        for o in items
    ]
    return Page[AdminOrderOut](items=out, total=total, page=page, page_size=page_size)


@router.get('/orders/{order_id}', response_model=OrderOut, summary='訂單詳情（後台）')
def get_order(order_id: IdPath, db: DB) -> OrderOut:
    return OrderOut.model_validate(admin_service.get_order(db, order_id))


@router.post('/orders/{order_id}/transition', response_model=OrderOut, summary='改變訂單狀態（出貨、完成、取消）')
def transition(order_id: IdPath, data: TransitionIn, db: DB) -> OrderOut:
    return OrderOut.model_validate(admin_service.transition_order(db, order_id, data.to_status))
