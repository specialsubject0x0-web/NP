"""購物車與地址 API（US-003、US-004）。全部需要登入，只能操作自己的資料。"""

from typing import Annotated

from fastapi import APIRouter, Path, Response

from app.core.deps import DB, CurrentUser
from app.schemas.cart import AddressIn, AddressOut, CartItemIn, CartOut
from app.schemas.common import ErrorResponse
from app.services import cart_service

router = APIRouter(tags=['cart'], responses={401: {'model': ErrorResponse}, 403: {'model': ErrorResponse}})
IdPath = Annotated[int, Path(gt=0, le=2_147_483_647)]


@router.get('/cart', response_model=CartOut, summary='我的購物車')
def get_cart(user: CurrentUser, db: DB) -> CartOut:
    return cart_service.get_cart(db, user)


@router.put(
    '/cart/items/{product_id}',
    response_model=CartOut,
    responses={404: {'model': ErrorResponse}, 409: {'model': ErrorResponse}},
    summary='設定購物車中某商品的數量',
)
def set_item(product_id: IdPath, data: CartItemIn, user: CurrentUser, db: DB) -> CartOut:
    return cart_service.set_quantity(db, user, product_id, data.quantity)


@router.delete('/cart/items/{product_id}', response_model=CartOut, summary='從購物車移除商品')
def remove_item(product_id: IdPath, user: CurrentUser, db: DB) -> CartOut:
    return cart_service.remove_item(db, user, product_id)


@router.get('/addresses', response_model=list[AddressOut], summary='我的收件地址')
def list_addresses(user: CurrentUser, db: DB) -> list[AddressOut]:
    return [AddressOut.model_validate(a) for a in cart_service.list_addresses(db, user)]


@router.post('/addresses', response_model=AddressOut, status_code=201, summary='新增收件地址')
def add_address(data: AddressIn, user: CurrentUser, db: DB) -> AddressOut:
    return AddressOut.model_validate(cart_service.add_address(db, user, data))


@router.delete('/addresses/{address_id}', status_code=204, responses={404: {'model': ErrorResponse}}, summary='刪除收件地址')
def delete_address(address_id: IdPath, user: CurrentUser, db: DB) -> Response:
    cart_service.delete_address(db, user, address_id)
    return Response(status_code=204)
