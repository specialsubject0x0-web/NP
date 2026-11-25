"""Migration 測試：執行 Alembic 後的資料表結構必須和 models 一致（防止忘記產生 Migration）。"""

from pathlib import Path

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine

from app.models import Base

BACKEND = Path(__file__).resolve().parents[1]


def test_migrations_match_models(tmp_path: Path) -> None:
    url = f'sqlite:///{tmp_path / "mig.db"}'
    cfg = Config(str(BACKEND / 'alembic.ini'))
    cfg.set_main_option('script_location', str(BACKEND / 'migrations'))
    cfg.set_main_option('sqlalchemy.url', url)
    cfg.attributes['configure_logger'] = False
    command.upgrade(cfg, 'head')
    engine = create_engine(url)
    with engine.connect() as conn:
        diff = compare_metadata(MigrationContext.configure(conn), Base.metadata)
    engine.dispose()
    assert diff == []
    command.downgrade(cfg, 'base')
