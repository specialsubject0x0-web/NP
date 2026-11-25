"""會員與登入狀態的資料表。

【重要】password_hash 只存雜湊，絕不存明碼；也絕不能出現在 API 回應（schemas 不包含它）。
"""

from datetime import datetime

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UTCDateTime, utcnow


class User(Base):
    """會員。role 為 member（一般會員）或 admin（管理員）。"""

    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)  # 一律存小寫
    password_hash: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(50))
    role: Mapped[str] = mapped_column(String(20), default='member')
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)


class UserSession(Base):
    """登入狀態（Session）。token_hash 是瀏覽器 Cookie 裡 token 的 SHA-256，不存原值。"""

    __tablename__ = 'sessions'

    id: Mapped[int] = mapped_column(primary_key=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    csrf_token: Mapped[str] = mapped_column(String(64))
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
