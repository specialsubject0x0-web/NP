"""US-009、US-010 後台（R-07、R-08、R-14）。"""

from typing import Any

import pytest

from tests.conftest import place_order

NEW = {'name': '新商品', 'description': '說明', 'price': 100, 'stock': 5, 'category_id': 1}


def test_admin_api_permissions(client: Any, member: Any) -> None:
    assert client.get('/api/v1/admin/products').status_code == 401
    res = member.get('/api/v1/admin/products')
    assert res.status_code == 403 and res.json()['code'] == 'FORBIDDEN'
    assert member.post('/api/v1/admin/products', json=NEW).status_code == 403
    assert member.post('/api/v1/admin/orders/1/transition', json={'to_status': 'shipped'}).status_code == 403


def test_create_and_update_product(admin: Any, client: Any) -> None:
    created = admin.post('/api/v1/admin/products', json=NEW).json()
    assert created['is_active'] is True and created['image_color'] == '#94a3b8'
    updated = admin.patch(f'/api/v1/admin/products/{created["id"]}', json={'price': 150, 'stock': 9}).json()
    assert (updated['price'], updated['stock']) == (150, 9)
    hidden = admin.patch(f'/api/v1/admin/products/{created["id"]}', json={'is_active': False}).json()
    assert hidden['is_active'] is False
    assert admin.get('/api/v1/admin/products', params={'page_size': 50}).json()['total'] == 17
    assert client.get('/api/v1/products').json()['total'] == 16


@pytest.mark.parametrize(
    'body',
    [{**NEW, 'price': -1}, {**NEW, 'stock': -1}, {**NEW, 'price': 1.5}, {**NEW, 'image_color': 'red'}, {**NEW, 'id': 1}],
)
def test_invalid_product_rejected(admin: Any, body: dict[str, Any]) -> None:
    assert admin.post('/api/v1/admin/products', json=body).status_code == 422


def test_product_edge_cases(admin: Any) -> None:
    assert admin.post('/api/v1/admin/products', json={**NEW, 'category_id': 999}).json()['code'] == 'CATEGORY_NOT_FOUND'
    assert admin.patch('/api/v1/admin/products/999', json={'price': 1}).status_code == 404
    assert admin.patch('/api/v1/admin/products/1', json={'price': None}).status_code == 422
    assert admin.patch('/api/v1/admin/products/1', json={'category_id': 999}).status_code == 422


def test_order_lifecycle(admin: Any, member: Any) -> None:
    oid = place_order(member, {1: 1}).json()['id']
    res = admin.post(f'/api/v1/admin/orders/{oid}/transition', json={'to_status': 'shipped'})
    assert res.status_code == 409  # 還沒付款不能出貨
    member.post(f'/api/v1/orders/{oid}/payments', headers={'Idempotency-Key': 'pay-key-0001'})
    for step in ('shipped', 'completed'):
        assert admin.post(f'/api/v1/admin/orders/{oid}/transition', json={'to_status': step}).json()['status'] == step
    res = admin.post(f'/api/v1/admin/orders/{oid}/transition', json={'to_status': 'cancelled'})
    assert res.status_code == 409 and res.json()['details'] == {'from': 'completed', 'to': 'cancelled'}
    assert admin.post(f'/api/v1/admin/orders/{oid}/transition', json={'to_status': 'paid'}).status_code == 422
    assert admin.get(f'/api/v1/admin/orders/{oid}').json()['status'] == 'completed'
    assert admin.get('/api/v1/admin/orders/999').status_code == 404
    assert admin.post('/api/v1/admin/orders/999/transition', json={'to_status': 'shipped'}).status_code == 404


def test_admin_cancel_and_list_filter(admin: Any, member: Any) -> None:
    a = place_order(member, {1: 1}, key='admin-key-0001').json()['id']
    place_order(member, {5: 1}, key='admin-key-0002')
    assert admin.post(f'/api/v1/admin/orders/{a}/transition', json={'to_status': 'cancelled'}).json()['status'] == 'cancelled'
    body = admin.get('/api/v1/admin/orders', params={'status': 'cancelled'}).json()
    assert body['total'] == 1 and body['items'][0]['recipient_name'] == '王小明'
    assert admin.get('/api/v1/admin/orders').json()['total'] == 2
    assert admin.get('/api/v1/admin/orders', params={'status': 'hacked'}).status_code == 422
