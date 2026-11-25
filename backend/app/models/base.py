"""所有資料表共用的基礎設定。

【重要】時間一律存 UTC（世界標準時間），前端顯示時再轉成台灣時間。
SQLite 不會記住時區，所以用 UTCDateTime 這個型別：存進去前轉成 UTC，讀出來時補回 UTC 標記。
"""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import DateTime
from sqlalchemy.engine import Dialect
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.types import TypeDecorator


def utcnow() -> datetime:
    """現在時間（UTC，帶時區）。"""
    return datetime.now(UTC)


class UTCDateTime(TypeDecorator[datetime]):
    """存取時都保證是 UTC 的時間欄位。"""

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value.astimezone(UTC).replace(tzinfo=None)

    def process_result_value(self, value: Any, dialect: Dialect) -> datetime | None:
        if not isinstance(value, datetime):
            return None
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


class Base(DeclarativeBase):
    """所有資料表類別都繼承它。"""
