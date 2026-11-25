"""FastAPI 的「依賴」：在每個 API 執行前自動做的檢查（登入、權限、CSRF、限速）。

名詞：
- CSRF（跨站請求偽造）：壞網站偷偷用你的登入狀態送出請求。防法：要求請求帶上一個只有我們網站讀得到的 token。
【重要】前端隱藏按鈕不等於授權；權限一律在這裡由後端檢查（AGENTS.md 5.3）。
"""

from typing import Annotated

from fastapi import Depends, Header, Request
from sqlalchemy.orm import Session

from app.core import rate_limit
from app.core.database import get_db
from app.core.errors import AppError
from app.core.security import hash_token, tokens_equal
from app.models import User
from app.models.base import utcnow
from app.repositories import user_repo

SESSION_COOKIE = 'shop_session'
CSRF_COOKIE = 'shop_csrf'
CSRF_HEADER = 'X-CSRF-Token'
SAFE_METHODS = frozenset({'GET', 'HEAD', 'OPTIONS'})
# 金流回呼是「金流伺服器」打來的，沒有瀏覽器 Cookie，改用簽章驗證（R-10）
CSRF_EXEMPT_PATHS = frozenset({'/api/v1/payments/callback'})

DB = Annotated[Session, Depends(get_db)]


def csrf_protect(request: Request) -> None:
    """會改變資料的請求（POST/PUT/PATCH/DELETE）必須帶 X-CSRF-Token，且要等於 Cookie 中的值（R-17）。"""
    if request.method in SAFE_METHODS or request.url.path in CSRF_EXEMPT_PATHS:
        return
    if not tokens_equal(request.headers.get(CSRF_HEADER), request.cookies.get(CSRF_COOKIE)):
        raise AppError(403, 'CSRF_FAILED', '安全驗證失敗，請重新整理頁面後再試')


def get_optional_user(request: Request, db: DB) -> User | None:
    """有登入就回傳會員，沒登入回傳 None。"""
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return None
    found = user_repo.get_session_user(db, hash_token(token), utcnow())
    if found is None:
        return None
    session, user = found
    # CSRF token 也必須是「這個 Session 發的那一個」，防止別人塞自己的 CSRF Cookie
    if request.method not in SAFE_METHODS and not tokens_equal(request.cookies.get(CSRF_COOKIE), session.csrf_token):
        raise AppError(403, 'CSRF_FAILED', '安全驗證失敗，請重新整理頁面後再試')
    return user


def get_current_user(user: Annotated[User | None, Depends(get_optional_user)]) -> User:
    """必須登入（R-04）；沒登入 → 401。"""
    if user is None:
        raise AppError(401, 'AUTH_REQUIRED', '請先登入')
    return user


def require_admin(user: Annotated[User, Depends(get_current_user)]) -> User:
    """必須是管理員（R-14）；一般會員 → 403。"""
    if user.role != 'admin':
        raise AppError(403, 'FORBIDDEN', '沒有權限')
    return user


def order_rate_limit(user: Annotated[User, Depends(get_current_user)]) -> User:
    """下單、試算的限速（R-15）。"""
    if not rate_limit.order_actions.hit(f'user:{user.id}'):
        raise AppError(429, 'TOO_MANY_REQUESTS', '操作太頻繁，請稍後再試')
    return user


def idempotency_key(key: Annotated[str | None, Header(alias='Idempotency-Key')] = None) -> str:
    """讀取 Idempotency-Key 標頭（R-11）。必須是 8–64 個英數或 - _ 字元。"""
    if key is None or not (8 <= len(key) <= 64) or not all(c.isascii() and (c.isalnum() or c in '-_') for c in key):
        raise AppError(400, 'IDEMPOTENCY_KEY_REQUIRED', '缺少或格式錯誤的 Idempotency-Key')
    return key


CurrentUser = Annotated[User, Depends(get_current_user)]
AdminUser = Annotated[User, Depends(require_admin)]
RateLimitedUser = Annotated[User, Depends(order_rate_limit)]
IdempotencyKey = Annotated[str, Depends(idempotency_key)]
