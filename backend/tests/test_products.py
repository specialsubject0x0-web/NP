"""US-001、US-002 瀏覽與搜尋商品（R-18）。"""

from typing import Any

import pytest


def test_list_products_default_paging(client: Any) -> None:
    body = client.get('/api/v1/products').json()
    assert body['total'] == 16 and body['page'] == 1 and len(body['items']) == 12
    assert body['items'][0]['currency'] == 'TWD'


def test_search_keyword_and_filters(client: Any) -> None:
    body = client.get('/api/v1/products', params={'q': '杯'}).json()
    assert body['total'] >= 2 and all('杯' in p['name'] or '杯' in p['description'] for p in body['items'])
    cat = client.get('/api/v1/products', params={'category_id': 2}).json()
    assert cat['total'] == 4 and all(p['category_id'] == 2 for p in cat['items'])
    rng = client.get('/api/v1/products', params={'min_price': 500, 'max_price': 800}).json()
    assert rng['total'] > 0 and all(500 <= p['price'] <= 800 for p in rng['items'])


def test_like_wildcards_are_escaped(client: Any) -> None:
    assert client.get('/api/v1/products', params={'q': '%'}).json()['total'] == 0
    assert client.get('/api/v1/products', params={'q': '_'}).json()['total'] == 0


@pytest.mark.parametrize(
    ('sort', 'key', 'reverse'), [('price_asc', 'price', False), ('price_desc', 'price', True), ('name', 'name', False)]
)
def test_sorting(client: Any, sort: str, key: str, reverse: bool) -> None:
    items = client.get('/api/v1/products', params={'sort': sort, 'page_size': 50}).json()['items']
    values = [p[key] for p in items]
    assert values == sorted(values, reverse=reverse)


@pytest.mark.parametrize(
    'params',
    [{'sort': 'password'}, {'page_size': 500}, {'page': 0}, {'category_id': -1}, {'min_price': -5}, {'unknown': 1}, {'q': 'x' * 51}],
)
def test_invalid_query_rejected(client: Any, params: dict[str, Any]) -> None:
    res = client.get('/api/v1/products', params=params)
    assert res.status_code == 422 and res.json()['code'] == 'VALIDATION_ERROR'


def test_min_price_greater_than_max_rejected(client: Any) -> None:
    res = client.get('/api/v1/products', params={'min_price': 900, 'max_price': 100})
    assert res.status_code == 422 and res.json()['code'] == 'INVALID_PRICE_RANGE'


def test_sql_injection_text_is_harmless(client: Any) -> None:
    res = client.get('/api/v1/products', params={'q': "' OR 1=1 --"})
    assert res.status_code == 200 and res.json()['total'] == 0


def test_product_detail_and_not_found(client: Any, admin: Any) -> None:
    assert client.get('/api/v1/products/1').json()['name'] == '手沖咖啡濾杯'
    for bad in ('0', '-1', '99999'):
        res = client.get(f'/api/v1/products/{bad}')
        assert res.status_code in (404, 422)
        assert 'Traceback' not in res.text
    assert admin.patch('/api/v1/admin/products/1', json={'is_active': False}).status_code == 200
    assert client.get('/api/v1/products/1').json()['code'] == 'PRODUCT_NOT_FOUND'
    assert all(p['id'] != 1 for p in client.get('/api/v1/products', params={'page_size': 50}).json()['items'])


def test_categories(client: Any) -> None:
    assert [c['slug'] for c in client.get('/api/v1/categories').json()] == ['kitchen', 'stationery', 'living', 'tech']


def test_unknown_route_uses_error_format(client: Any) -> None:
    res = client.get('/api/v1/nothing-here')
    assert res.status_code == 404 and res.json()['code'] == 'NOT_FOUND'
    res = client.delete('/api/v1/products')
    assert res.status_code == 405 and res.json()['code'] == 'METHOD_NOT_ALLOWED'
