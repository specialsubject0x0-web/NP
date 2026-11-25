"""會員與 Session 的資料存取。只負責查詢與寫入，不判斷商業規則。"""

from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import User, UserSession


def get_by_email(db: Session, email: str) -> User | None:
    """依 Email（小寫）找會員。"""
    return db.scalar(select(User).where(User.email == email.lower()))


def get_session_user(db: Session, token_hash: str, now: datetime) -> tuple[UserSession, User] | None:
    """依 token 雜湊找「尚未過期」的 Session 與會員。"""
    row = db.execute(
        select(UserSession, User)
        .join(User, User.id == UserSession.user_id)
        .where(UserSession.token_hash == token_hash, UserSession.expires_at > now)
    ).first()
    return (row[0], row[1]) if row else None


def delete_session(db: Session, token_hash: str) -> None:
    """登出：刪除這個 Session。"""
    db.execute(delete(UserSession).where(UserSession.token_hash == token_hash))
