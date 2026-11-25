"""Alembic 設定：Migration（資料庫結構變更腳本）執行時會讀這個檔案。

資料庫網址來自 app 的設定（.env 的 SHOP_DATABASE_URL），不用另外改 alembic.ini。
新增或修改資料表後，在 backend/ 執行：uv run alembic revision --autogenerate -m "說明"，再檢查產生的檔案。
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import get_settings
from app.models import Base

config = context.config
if config.config_file_name is not None and config.attributes.get('configure_logger', True):
    fileConfig(config.config_file_name)

if not config.get_main_option('sqlalchemy.url'):
    config.set_main_option('sqlalchemy.url', get_settings().database_url)
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option('sqlalchemy.url'), target_metadata=target_metadata, literal_binds=True, render_as_batch=True
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(config.get_section(config.config_ini_section, {}), prefix='sqlalchemy.', poolclass=pool.NullPool)
    with connectable.connect() as connection:
        # render_as_batch：讓 SQLite 也能修改欄位（SQLite 的 ALTER TABLE 功能很少）
        context.configure(connection=connection, target_metadata=target_metadata, render_as_batch=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
