"""US-003 購物車、US-004 地址（R-04、R-05、R-13）。"""

from typing import Any

import pytest

from tests.conftest import ADDRESS, add_address, put_cart


def test_cart_requires_login(client: Any) -> None:
    assert client.get('/api/v1/cart').status_code == 401
    assert put_cart(client, 1, 1).status_code == 401


def test_add_update_remove(member: Any) -> None:
    body = put_cart(member, 1, 2).json()
    assert body['items'][0]['line_total'] == 1360 and body['subtotal'] == 1360 and body['item_count'] == 2
    body = put_cart(member, 1, 3).json()  # 設定數量，不是累加
    assert body['items'][0]['quantity'] == 3
    put_cart(member, 5, 1)
    body = member.delete('/api/v1/cart/items/1').json()
    assert [i['product_id'] for i in body['items']] == [5]


@pytest.mark.parametrize('qty', [0, -1, 100, 999999999])
def test_invalid_quantity(member: Any, qty: int) -> None:
    assert put_cart(member, 1, qty).status_code == 422


def test_quantity_over_stock(member: Any) -> None:
    res = put_cart(member, 12, 2)  # 限量陶杯只有 1 件
    assert res.status_code == 409 and res.json()['details']['stock'] == 1
    assert member.get('/api/v1/cart').json()['items'] == []


def test_inactive_or_missing_product(member: Any, admin: Any) -> None:
    assert put_cart(member, 99999, 1).status_code == 404
    assert put_cart(member, 16, 1).status_code == 409  # 庫存 0
    put_cart(member, 2, 1)
    admin.patch('/api/v1/admin/products/2', json={'is_active': False})
    assert member.get('/api/v1/cart').json()['items'][0]['is_available'] is False
    assert put_cart(member, 2, 1).status_code == 404


def test_address_crud_and_validation(member: Any) -> None:
    aid = add_address(member)
    assert member.get('/api/v1/addresses').json()[0]['recipient'] == ADDRESS['recipient']
    assert member.post('/api/v1/addresses', json={**ADDRESS, 'phone': '12345'}).status_code == 422
    assert member.post('/api/v1/addresses', json={**ADDRESS, 'user_id': 1}).status_code == 422
    assert member.delete(f'/api/v1/addresses/{aid}').status_code == 204
    assert member.get('/api/v1/addresses').json() == []


def test_cannot_touch_other_members_address(member: Any, other_member: Any) -> None:
    aid = add_address(member)
    res = other_member.delete(f'/api/v1/addresses/{aid}')
    assert res.status_code == 404 and res.json()['code'] == 'ADDRESS_NOT_FOUND'
    assert other_member.get('/api/v1/addresses').json() == []
    assert len(member.get('/api/v1/addresses').json()) == 1


def test_carts_are_separate(member: Any, other_member: Any) -> None:
    put_cart(member, 1, 1)
    assert other_member.get('/api/v1/cart').json()['items'] == []
