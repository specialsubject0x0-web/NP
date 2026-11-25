"""測試共用設定：每個測試都用一個全新的暫存資料庫，並放入示範資料。

ApiClient 會自動帶上 CSRF 標頭（模擬前端的行為），讓每個測試只專心寫要測的事。
"""

import os

os.environ['SHOP_ENV'] = 'test'
os.environ['SHOP_PAYMENT_WEBHOOK_SECRET'] = 'test-secret'

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.core import rate_limit
from app.core.config import get_settings
from app.core.database import get_db, make_engine
from app.core.deps import CSRF_COOKIE, CSRF_HEADER
from app.main import app
from app.models import Base
from scripts.seed import seed

get_settings.cache_clear()

NO_CSRF = 'X-Test-No-Csrf'
ADMIN = ('admin@example.com', 'admin12345')
DEMO = ('demo@example.com', 'demo12345')


@pytest.fixture
def session_factory(tmp_path: Path) -> Iterator[sessionmaker[Session]]:
    engine = make_engine(f'sqlite:///{tmp_path / "test.db"}')
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with factory() as db:
        seed(db)
    rate_limit.reset_all()
    yield factory
    engine.dispose()


@pytest.fixture
def db(session_factory: sessionmaker[Session]) -> Iterator[Session]:
    with session_factory() as session:
        yield session


class ApiClient(TestClient):
    """會自動附上 CSRF token 的測試用瀏覽器。"""

    def request(self, method: str, url: Any, *args: Any, **kwargs: Any) -> Any:  # type: ignore[override]
        headers = dict(kwargs.pop('headers', None) or {})
        # 測試想故意「不帶 CSRF」時，加上 NO_CSRF 標頭（送出前會移除）
        skip = headers.pop(NO_CSRF, None) is not None
        kwargs['headers'] = headers
        if method.upper() not in {'GET', 'HEAD', 'OPTIONS'} and not skip:
            token = self.cookies.get(CSRF_COOKIE)
            if token is None:
                super().request('GET', '/api/v1/auth/csrf')
                token = self.cookies.get(CSRF_COOKIE)
            headers.setdefault(CSRF_HEADER, token)
        return super().request(method, url, *args, **kwargs)

    def set_csrf_cookie(self, value: str) -> None:
        """把 CSRF Cookie 換成指定值（模擬攻擊者塞入自己的 Cookie）。"""
        self.cookies.delete(CSRF_COOKIE)
        self.cookies.set(CSRF_COOKIE, value)

    def login(self, email: str, password: str) -> ApiClient:
        res = self.post('/api/v1/auth/login', json={'email': email, 'password': password})
        assert res.status_code == 200, res.text
        return self


@pytest.fixture
def make_client(session_factory: sessionmaker[Session]) -> Iterator[Any]:
    def _get_db() -> Iterator[Session]:
        with session_factory() as s:
            yield s

    app.dependency_overrides[get_db] = _get_db
    clients: list[ApiClient] = []

    def factory() -> ApiClient:
        c = ApiClient(app)
        clients.append(c)
        return c

    yield factory
    for c in clients:
        c.close()
    app.dependency_overrides.clear()


@pytest.fixture
def client(make_client: Any) -> ApiClient:
    """未登入的訪客。"""
    c: ApiClient = make_client()
    return c


@pytest.fixture
def member(make_client: Any) -> ApiClient:
    """已登入的示範會員。"""
    c: ApiClient = make_client()
    return c.login(*DEMO)


@pytest.fixture
def admin(make_client: Any) -> ApiClient:
    """已登入的管理員。"""
    c: ApiClient = make_client()
    return c.login(*ADMIN)


@pytest.fixture
def other_member(make_client: Any) -> ApiClient:
    """另一位會員（測越權用）。"""
    c: ApiClient = make_client()
    res = c.post('/api/v1/auth/register', json={'email': 'other@example.com', 'password': 'other12345', 'name': '別人'})
    assert res.status_code == 201
    return c


ADDRESS = {'recipient': '王小明', 'phone': '0912345678', 'postal_code': '100', 'city': '台北市', 'line': '中正區重慶南路一段 1 號'}


def add_address(c: ApiClient) -> int:
    res = c.post('/api/v1/addresses', json=ADDRESS)
    assert res.status_code == 201, res.text
    return int(res.json()['id'])


def put_cart(c: ApiClient, product_id: int, qty: int) -> Any:
    return c.put(f'/api/v1/cart/items/{product_id}', json={'quantity': qty})


def place_order(c: ApiClient, items: dict[int, int], key: str = 'order-key-0001', coupon: str | None = None) -> Any:
    """把商品放進購物車並下單，回傳 response。"""
    for pid, qty in items.items():
        assert put_cart(c, pid, qty).status_code == 200
    body: dict[str, Any] = {'address_id': add_address(c)}
    if coupon:
        body['coupon_code'] = coupon
    return c.post('/api/v1/orders', json=body, headers={'Idempotency-Key': key})
