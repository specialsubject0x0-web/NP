"""安全設定：安全標頭、CORS、錯誤不洩露細節、正式環境設定檢查。"""

from typing import Any

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import DEV_ONLY_SECRET, Settings
from app.core.rate_limit import RateLimiter
from app.core.security import hash_password, verify_password
from app.main import create_app


def test_security_headers(client: Any) -> None:
    res = client.get('/api/v1/health')
    assert res.json() == {'status': 'ok'}
    assert res.headers['X-Content-Type-Options'] == 'nosniff'
    assert res.headers['X-Frame-Options'] == 'DENY'
    assert "default-src 'none'" in res.headers['Content-Security-Policy']
    assert res.headers['Cache-Control'] == 'no-store'


def test_cors_whitelist(client: Any) -> None:
    ok = client.options('/api/v1/products', headers={'Origin': 'http://localhost:5173', 'Access-Control-Request-Method': 'GET'})
    assert ok.headers.get('access-control-allow-origin') == 'http://localhost:5173'
    assert ok.headers.get('access-control-allow-credentials') == 'true'
    bad = client.get('/api/v1/products', headers={'Origin': 'https://evil.example'})
    assert 'access-control-allow-origin' not in bad.headers


def test_unexpected_error_hides_details() -> None:
    app = create_app(Settings(env='test'))

    @app.get('/boom')
    def boom() -> None:
        raise RuntimeError('secret internal detail')

    res = TestClient(app, raise_server_exceptions=False).get('/boom')
    assert res.status_code == 500 and res.json()['code'] == 'INTERNAL_ERROR'
    assert 'secret' not in res.text


def test_production_requires_real_secret_and_hides_docs() -> None:
    with pytest.raises(ValidationError):
        Settings(env='production', payment_webhook_secret=DEV_ONLY_SECRET)
    with pytest.raises(ValidationError):
        Settings(env='test', cors_origins=['*'])
    prod = Settings(env='production', payment_webhook_secret='a-real-long-secret')
    assert prod.cookie_secure is True
    assert TestClient(create_app(prod)).get('/docs').status_code == 404


def test_password_hashing() -> None:
    h = hash_password('correct-horse')
    assert h.startswith('$argon2') and 'correct-horse' not in h
    assert verify_password('correct-horse', h) is True
    assert verify_password('wrong', h) is False
    assert verify_password('correct-horse', None) is False
    assert verify_password('x', 'not-a-hash') is False


def test_rate_limiter_window() -> None:
    limiter = RateLimiter(2, 60)
    assert limiter.hit('a') and limiter.hit('a') and not limiter.hit('a')
    assert limiter.is_blocked('a') and not limiter.is_blocked('b')
    limiter.reset('a')
    assert not limiter.is_blocked('a')
    limiter.window = -1  # 讓舊紀錄立即過期
    assert limiter.hit('a')
