"""註冊、登入、登出的商業規則（US-008）。

流程：登入成功 → 產生隨機 session token 與 CSRF token → token 雜湊後存資料庫 → 原值放進 Cookie 交給瀏覽器。
"""

from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core import rate_limit
from app.core.config import get_settings
from app.core.errors import AppError
from app.core.security import hash_password, hash_token, new_token, verify_password
from app.models import User, UserSession
from app.models.base import utcnow
from app.repositories import user_repo
from app.schemas.auth import LoginIn, RegisterIn


@dataclass(frozen=True)
class LoginResult:
    """登入結果：會員、要放進 Cookie 的 session token 與 CSRF token。"""

    user: User
    session_token: str
    csrf_token: str


def _start_session(db: Session, user: User) -> LoginResult:
    token, csrf = new_token(), new_token()
    expires = utcnow() + timedelta(days=get_settings().session_days)
    db.add(UserSession(token_hash=hash_token(token), csrf_token=csrf, user_id=user.id, expires_at=expires))
    db.commit()
    return LoginResult(user=user, session_token=token, csrf_token=csrf)


def register(db: Session, data: RegisterIn) -> LoginResult:
    """註冊新會員，成功後直接登入。Email 重複（不分大小寫）→ 409（R-16）。"""
    email = data.email.lower()
    if user_repo.get_by_email(db, email):
        raise AppError(409, 'EMAIL_TAKEN', '這個 Email 已經註冊過了')
    user = User(email=email, password_hash=hash_password(data.password), name=data.name, role='member')
    db.add(user)
    try:
        db.flush()
    except IntegrityError:
        # 兩個人同時用同一個 Email 註冊：資料庫的唯一限制擋下第二個
        db.rollback()
        raise AppError(409, 'EMAIL_TAKEN', '這個 Email 已經註冊過了') from None
    return _start_session(db, user)


def login(db: Session, data: LoginIn, client_ip: str) -> LoginResult:
    """登入。連續失敗太多次 → 429（R-15）。

    【重要】錯誤訊息一律是「Email 或密碼錯誤」，不告訴對方是哪一個錯（避免被用來猜哪些 Email 有註冊）。
    """
    email = data.email.lower()
    key = f'{client_ip}:{email}'
    if rate_limit.login_failures.is_blocked(key):
        raise AppError(429, 'TOO_MANY_ATTEMPTS', '登入失敗次數過多，請 5 分鐘後再試')
    user = user_repo.get_by_email(db, email)
    if not verify_password(data.password, user.password_hash if user else None) or user is None:
        rate_limit.login_failures.hit(key)
        raise AppError(401, 'INVALID_CREDENTIALS', 'Email 或密碼錯誤')
    rate_limit.login_failures.reset(key)
    return _start_session(db, user)


def logout(db: Session, session_token: str | None) -> None:
    """登出：刪除伺服器上的 Session（光刪 Cookie 不夠，要讓舊 token 失效）。"""
    if session_token:
        user_repo.delete_session(db, hash_token(session_token))
        db.commit()
