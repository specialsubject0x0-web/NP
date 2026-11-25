"""資料庫連線。

誰會用到：每個 API 請求透過 get_db() 拿到一個資料庫 Session（工作階段），請求結束自動關閉。
想換資料庫：改 .env 的 SHOP_DATABASE_URL，例如 postgresql+psycopg://user:pass@host/shop（需另外安裝驅動，須經人同意）。
"""

from collections.abc import Iterator
from typing import Any

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


def make_engine(url: str) -> Engine:
    """建立資料庫引擎。SQLite 需要額外設定才能在多執行緒（多個請求）下使用。"""
    connect_args: dict[str, Any] = {}
    if url.startswith('sqlite'):
        # 【為什麼】timeout：同時有人寫入時等一下，而不是馬上報「database is locked」
        connect_args = {'check_same_thread': False, 'timeout': 30}
    engine = create_engine(url, connect_args=connect_args)
    if url.startswith('sqlite'):

        @event.listens_for(engine, 'connect')
        def _sqlite_pragmas(dbapi_conn: Any, _record: Any) -> None:
            # 【為什麼】SQLite 預設不檢查外鍵，要手動打開，資料才不會指向不存在的東西
            cursor = dbapi_conn.cursor()
            cursor.execute('PRAGMA foreign_keys=ON')
            cursor.close()

    return engine


engine = make_engine(get_settings().database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    """FastAPI 依賴：給每個請求一個資料庫 Session，用完一定關閉。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
