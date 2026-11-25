"""US-008 註冊與登入（R-15、R-16、R-17）。"""

from typing import Any

from tests.conftest import DEMO, NO_CSRF

REG = {'email': 'New@Example.com', 'password': 'password123', 'name': '新會員'}


def test_register_logs_in_with_httponly_cookie(client: Any) -> None:
    res = client.post('/api/v1/auth/register', json=REG)
    assert res.status_code == 201
    body = res.json()
    assert body['email'] == 'new@example.com'  # Email 一律存小寫
    assert 'password_hash' not in body and 'password' not in body
    cookies = res.headers.get_list('set-cookie')
    session_cookie = next(c for c in cookies if c.startswith('shop_session='))
    assert 'HttpOnly' in session_cookie and 'SameSite=lax' in session_cookie
    assert client.get('/api/v1/auth/me').json()['email'] == 'new@example.com'


def test_register_duplicate_email_case_insensitive(client: Any) -> None:
    assert client.post('/api/v1/auth/register', json=REG).status_code == 201
    res = client.post('/api/v1/auth/register', json={**REG, 'email': 'NEW@example.com'})
    assert res.status_code == 409 and res.json()['code'] == 'EMAIL_TAKEN'


def test_register_short_password_and_extra_field_rejected(client: Any) -> None:
    assert client.post('/api/v1/auth/register', json={**REG, 'password': 'short'}).status_code == 422
    res = client.post('/api/v1/auth/register', json={**REG, 'role': 'admin'})  # 想偷偷註冊成管理員
    assert res.status_code == 422 and res.json()['code'] == 'VALIDATION_ERROR'


def test_login_wrong_password_and_unknown_email_same_message(client: Any) -> None:
    a = client.post('/api/v1/auth/login', json={'email': DEMO[0], 'password': 'wrong-pass'})
    b = client.post('/api/v1/auth/login', json={'email': 'nobody@example.com', 'password': 'wrong-pass'})
    assert a.status_code == b.status_code == 401
    assert a.json() == b.json()


def test_login_rate_limited_after_five_failures(client: Any) -> None:
    for _ in range(5):
        assert client.post('/api/v1/auth/login', json={'email': DEMO[0], 'password': 'bad-password'}).status_code == 401
    res = client.post('/api/v1/auth/login', json={'email': DEMO[0], 'password': DEMO[1]})
    assert res.status_code == 429 and res.json()['code'] == 'TOO_MANY_ATTEMPTS'


def test_logout_invalidates_session(member: Any) -> None:
    assert member.get('/api/v1/auth/me').status_code == 200
    assert member.post('/api/v1/auth/logout').status_code == 204
    assert member.get('/api/v1/auth/me').status_code == 401


def test_me_requires_login(client: Any) -> None:
    res = client.get('/api/v1/auth/me')
    assert res.status_code == 401 and res.json()['code'] == 'AUTH_REQUIRED'


def test_csrf_missing_header_rejected(member: Any) -> None:
    res = member.put('/api/v1/cart/items/1', json={'quantity': 1}, headers={NO_CSRF: '1'})
    assert res.status_code == 403 and res.json()['code'] == 'CSRF_FAILED'


def test_csrf_token_must_belong_to_session(member: Any) -> None:
    # 攻擊者塞了自己的 CSRF Cookie 與標頭：兩者相同，但不是這個 Session 發的 → 拒絕
    member.set_csrf_cookie('attacker-token')
    res = member.put('/api/v1/cart/items/1', json={'quantity': 1}, headers={'X-CSRF-Token': 'attacker-token'})
    assert res.status_code == 403


def test_csrf_endpoint_reuses_existing_token(client: Any) -> None:
    first = client.get('/api/v1/auth/csrf').json()['csrf_token']
    assert client.get('/api/v1/auth/csrf').json()['csrf_token'] == first


def test_expired_or_unknown_session_is_anonymous(client: Any) -> None:
    client.cookies.set('shop_session', 'not-a-real-token')
    assert client.get('/api/v1/auth/me').status_code == 401
