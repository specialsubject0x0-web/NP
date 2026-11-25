"""US-005 結帳、US-007 訂單（R-03、R-06、R-07、R-08、R-09、R-11、R-13）。"""

from typing import Any

import pytest
from sqlalchemy.orm import Session

from app.models import Product
from tests.conftest import add_address, place_order, put_cart


def quote(c: Any, coupon: str | None = None) -> Any:
    return c.post('/api/v1/checkout/quote', json={'coupon_code': coupon} if coupon else {})


@pytest.mark.parametrize(
    ('items', 'subtotal', 'shipping'),
    [({5: 5}, 900, 60), ({5: 1, 13: 1}, 470, 60), ({2: 1, 6: 1}, 1040, 0), ({3: 1, 13: 1, 5: 1}, 990, 60)],
)
def test_quote_shipping_rule(member: Any, items: dict[int, int], subtotal: int, shipping: int) -> None:
    for pid, qty in items.items():
        put_cart(member, pid, qty)
    body = quote(member).json()
    assert body['subtotal'] == subtotal and body['shipping_fee'] == shipping and body['total'] == subtotal + shipping


def test_quote_threshold_exactly_1000_is_free(member: Any, admin: Any) -> None:
    admin.patch('/api/v1/admin/products/5', json={'price': 200})
    put_cart(member, 5, 5)
    assert quote(member).json()['shipping_fee'] == 0


def test_quote_empty_cart(member: Any) -> None:
    res = quote(member)
    assert res.status_code == 409 and res.json()['code'] == 'CART_EMPTY'


def test_create_order_happy_path(member: Any, db: Session) -> None:
    res = place_order(member, {1: 2, 5: 1})
    assert res.status_code == 201
    order = res.json()
    assert order['status'] == 'pending_payment'
    assert order['subtotal'] == 1540 and order['shipping_fee'] == 0 and order['total'] == 1540
    assert order['items'][0] == {'product_id': 1, 'product_name': '手沖咖啡濾杯', 'unit_price': 680, 'quantity': 2, 'line_total': 1360}
    assert order['recipient_name'] == '王小明'
    assert order['created_at'].endswith('Z')  # 時間一律 UTC（ISO 8601）
    assert db.get(Product, 1).stock == 23  # type: ignore[union-attr]
    assert member.get('/api/v1/cart').json()['items'] == []


def test_idempotency_key_prevents_duplicate_orders(member: Any) -> None:
    first = place_order(member, {1: 1}, key='same-key-123')
    again = member.post('/api/v1/orders', json={'address_id': 1}, headers={'Idempotency-Key': 'same-key-123'})
    assert first.status_code == 201 and again.status_code == 200
    assert again.json()['id'] == first.json()['id']
    assert member.get('/api/v1/orders').json()['total'] == 1


@pytest.mark.parametrize('key', [None, 'short', 'has space key!', 'x' * 65])
def test_idempotency_key_required(member: Any, key: str | None) -> None:
    put_cart(member, 1, 1)
    aid = add_address(member)
    headers = {'Idempotency-Key': key} if key else {}
    res = member.post('/api/v1/orders', json={'address_id': aid}, headers=headers)
    assert res.status_code == 400 and res.json()['code'] == 'IDEMPOTENCY_KEY_REQUIRED'


@pytest.mark.parametrize('extra', [{'price': 1}, {'total': 1}, {'items': [{'product_id': 1, 'quantity': 1, 'price': 1}]}])
def test_tampered_price_fields_rejected(member: Any, extra: dict[str, Any]) -> None:
    put_cart(member, 1, 1)
    aid = add_address(member)
    res = member.post('/api/v1/orders', json={'address_id': aid, **extra}, headers={'Idempotency-Key': 'tamper-0001'})
    assert res.status_code == 422


def test_out_of_stock_rolls_back_everything(member: Any, admin: Any, db: Session) -> None:
    put_cart(member, 1, 2)
    put_cart(member, 12, 1)
    admin.patch('/api/v1/admin/products/12', json={'stock': 0})  # 放進購物車後被買走
    aid = add_address(member)
    res = member.post('/api/v1/orders', json={'address_id': aid}, headers={'Idempotency-Key': 'oos-key-0001'})
    assert res.status_code == 409 and res.json()['code'] == 'ORDER_OUT_OF_STOCK'
    assert db.get(Product, 1).stock == 25  # type: ignore[union-attr]  # 第一項也沒有被扣
    assert len(member.get('/api/v1/cart').json()['items']) == 2


def test_decrement_failure_inside_transaction_rolls_back(member: Any, monkeypatch: Any, db: Session) -> None:
    # 模擬「試算時還有庫存，扣庫存的瞬間被別人買走」：第二項扣庫存失敗
    from app.repositories import product_repo

    real = product_repo.decrement_stock
    monkeypatch.setattr(product_repo, 'decrement_stock', lambda d, pid, q: real(d, pid, q) if pid == 1 else False)
    res = place_order(member, {1: 1, 5: 1}, key='race-key-0001')
    assert res.status_code == 409
    db.expire_all()
    assert db.get(Product, 1).stock == 25  # type: ignore[union-attr]


def test_address_must_be_own(member: Any, other_member: Any) -> None:
    other_aid = add_address(other_member)
    put_cart(member, 1, 1)
    res = member.post('/api/v1/orders', json={'address_id': other_aid}, headers={'Idempotency-Key': 'addr-key-0001'})
    assert res.status_code == 404


def test_cannot_read_or_cancel_other_members_order(member: Any, other_member: Any) -> None:
    oid = place_order(member, {1: 1}).json()['id']
    assert other_member.get(f'/api/v1/orders/{oid}').status_code == 404
    assert other_member.post(f'/api/v1/orders/{oid}/cancel').status_code == 404
    assert other_member.get('/api/v1/orders').json()['total'] == 0
    assert member.get(f'/api/v1/orders/{oid}').status_code == 200


def test_orders_require_login(client: Any) -> None:
    assert client.get('/api/v1/orders').status_code == 401
    assert client.get('/api/v1/orders/1').status_code == 401


def test_cancel_restores_stock(member: Any, db: Session) -> None:
    oid = place_order(member, {1: 3}).json()['id']
    assert db.get(Product, 1).stock == 22  # type: ignore[union-attr]
    res = member.post(f'/api/v1/orders/{oid}/cancel')
    assert res.status_code == 200 and res.json()['status'] == 'cancelled'
    db.expire_all()
    assert db.get(Product, 1).stock == 25  # type: ignore[union-attr]
    again = member.post(f'/api/v1/orders/{oid}/cancel')
    assert again.status_code == 409 and again.json()['code'] == 'ORDER_INVALID_TRANSITION'


def test_price_snapshot_not_affected_by_price_change(member: Any, admin: Any) -> None:
    oid = place_order(member, {1: 1}).json()['id']
    admin.patch('/api/v1/admin/products/1', json={'price': 9999, 'name': '改名了'})
    item = member.get(f'/api/v1/orders/{oid}').json()['items'][0]
    assert item['unit_price'] == 680 and item['product_name'] == '手沖咖啡濾杯'


def test_order_list_paging(member: Any) -> None:
    for i in range(3):
        place_order(member, {5: 1}, key=f'paging-key-{i:04d}')
    body = member.get('/api/v1/orders', params={'page_size': 2}).json()
    assert body['total'] == 3 and len(body['items']) == 2 and body['items'][0]['item_count'] == 1
    assert member.get('/api/v1/orders', params={'page_size': 51}).status_code == 422


def test_order_rate_limit(member: Any) -> None:
    put_cart(member, 1, 1)
    codes = [quote(member).status_code for _ in range(21)]
    assert codes[:20] == [200] * 20 and codes[20] == 429
