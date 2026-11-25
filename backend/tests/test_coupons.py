"""US-011 優惠券（R-03、R-09、R-12）。"""

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models import Coupon
from app.services.pricing_service import coupon_discount
from tests.conftest import place_order, put_cart

NOW = datetime(2027, 6, 1, tzinfo=UTC)


def make_coupon(**kw: Any) -> Coupon:
    base: dict[str, Any] = {
        'code': 'T',
        'kind': 'fixed',
        'value': 100,
        'max_discount': None,
        'min_spend': 0,
        'starts_at': NOW - timedelta(days=1),
        'ends_at': NOW + timedelta(days=1),
        'usage_limit': None,
        'used_count': 0,
        'is_active': True,
    }
    base.update(kw)
    return Coupon(**base)


@pytest.mark.parametrize(
    ('coupon', 'subtotal', 'expected'),
    [
        (make_coupon(), 600, 100),
        (make_coupon(value=500), 300, 300),  # 折扣不超過小計
        (make_coupon(kind='percent', value=10), 999, 99),  # 無條件捨去
        (make_coupon(kind='percent', value=10, max_discount=200), 3000, 200),  # 上限
        (make_coupon(kind='percent', value=95), 1000, 900),  # 百分比最多 90%
    ],
)
def test_coupon_discount_math(coupon: Coupon, subtotal: int, expected: int) -> None:
    assert coupon_discount(coupon, subtotal, NOW) == expected


@pytest.mark.parametrize(
    ('coupon', 'code'),
    [
        (make_coupon(is_active=False), 'COUPON_NOT_FOUND'),
        (make_coupon(starts_at=NOW + timedelta(hours=1)), 'COUPON_NOT_STARTED'),
        (make_coupon(ends_at=NOW), 'COUPON_EXPIRED'),
        (make_coupon(min_spend=1000), 'COUPON_MIN_SPEND_NOT_MET'),
        (make_coupon(usage_limit=5, used_count=5), 'COUPON_USAGE_LIMIT_REACHED'),
    ],
)
def test_coupon_rejections(coupon: Coupon, code: str) -> None:
    with pytest.raises(AppError) as exc:
        coupon_discount(coupon, 600, NOW)
    assert exc.value.code == code


def quote(c: Any, code: Any) -> Any:
    return c.post('/api/v1/checkout/quote', json={'coupon_code': code})


def test_welcome100_example(member: Any) -> None:
    put_cart(member, 4, 1)
    put_cart(member, 13, 1)
    body = quote(member, 'welcome100').json()  # 大小寫不拘
    assert (body['subtotal'], body['discount'], body['shipping_fee'], body['total']) == (740, 100, 60, 700)
    assert body['coupon_code'] == 'WELCOME100'


def test_discount_can_drop_below_free_shipping(member: Any) -> None:
    put_cart(member, 2, 1)
    put_cart(member, 13, 1)  # 小計 1180
    body = quote(member, 'SAVE10').json()  # 折 118 → 1062，仍免運
    assert body['discount'] == 118 and body['shipping_fee'] == 0
    member.delete('/api/v1/cart/items/13')
    put_cart(member, 5, 1)  # 小計 1070，折 107 → 963 → 要運費（假設 A-03）
    body = quote(member, 'SAVE10').json()
    assert body['subtotal'] == 1070 and body['discount'] == 107 and body['shipping_fee'] == 60


@pytest.mark.parametrize(
    ('code', 'status', 'err'),
    [('EXPIRED50', 422, 'COUPON_EXPIRED'), ('NOPE', 422, 'COUPON_NOT_FOUND'), ('WELCOME100', 422, 'COUPON_MIN_SPEND_NOT_MET')],
)
def test_coupon_errors_via_api(member: Any, code: str, status: int, err: str) -> None:
    put_cart(member, 5, 1)  # 180 元，未達 500
    res = quote(member, code)
    assert res.status_code == status and res.json()['code'] == err


def test_two_coupons_rejected(member: Any) -> None:
    put_cart(member, 1, 1)
    assert quote(member, ['WELCOME100', 'SAVE10']).status_code == 422
    assert quote(member, 'WELCOME100,SAVE10').status_code == 422


def test_coupon_once_per_member_and_released_on_cancel(member: Any, db: Session) -> None:
    order = place_order(member, {1: 1}, coupon='WELCOME100').json()
    assert order['discount'] == 100 and order['coupon_code'] == 'WELCOME100'
    put_cart(member, 1, 1)
    res = quote(member, 'WELCOME100')
    assert res.status_code == 409 and res.json()['code'] == 'COUPON_ALREADY_USED'
    member.post(f'/api/v1/orders/{order["id"]}/cancel')
    assert quote(member, 'WELCOME100').status_code == 200
    assert db.scalar(select(Coupon.used_count).where(Coupon.code == 'WELCOME100')) == 0


def test_usage_limit_enforced_across_members(member: Any, other_member: Any, db: Session) -> None:
    coupon = db.scalar(select(Coupon).where(Coupon.code == 'SAVE10'))
    assert coupon is not None
    coupon.usage_limit = 1
    db.commit()
    assert place_order(member, {1: 1}, coupon='SAVE10').status_code == 201
    put_cart(other_member, 1, 1)
    res = quote(other_member, 'SAVE10')
    assert res.status_code == 409 and res.json()['code'] == 'COUPON_USAGE_LIMIT_REACHED'


def test_claim_fails_when_limit_reached_between_quote_and_order(member: Any, monkeypatch: Any, db: Session) -> None:
    from app.repositories import order_repo

    monkeypatch.setattr(order_repo, 'claim_coupon', lambda d, cid: False)
    res = place_order(member, {1: 1}, coupon='SAVE10')
    assert res.status_code == 409 and res.json()['code'] == 'COUPON_USAGE_LIMIT_REACHED'
    assert member.get('/api/v1/orders').json()['total'] == 0
