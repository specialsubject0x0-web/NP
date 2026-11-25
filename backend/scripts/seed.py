"""建立資料表並放入示範資料（只給開發與課堂展示用）。

執行：在 backend/ 執行 `uv run python -m scripts.seed`
會建立：4 個分類、16 個商品、3 張優惠券、1 個管理員、1 個示範會員。
帳號密碼來自 .env 的 SHOP_SEED_ADMIN_PASSWORD、SHOP_SEED_DEMO_PASSWORD（沒設定就用 admin12345／demo12345）。
【重要】正式環境不要執行這個腳本。已經有資料時不會重複新增。
"""

import json
from datetime import datetime
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models import Category, Coupon, Product, User

BASE = Path(__file__).resolve().parent.parent
DATA = json.loads((BASE / 'scripts' / 'seed_data.json').read_text(encoding='utf-8'))


def migrate() -> None:
    """執行所有 Migration，把資料表建到最新版本。"""
    cfg = Config(str(BASE / 'alembic.ini'))
    cfg.set_main_option('script_location', str(BASE / 'migrations'))
    cfg.attributes['configure_logger'] = False
    command.upgrade(cfg, 'head')


def seed(db: Session) -> None:
    if db.scalar(select(Product.id).limit(1)) is not None:
        print('已經有資料，略過。')
        return
    for c in DATA['categories']:
        db.add(Category(**c))
    db.flush()
    for p in DATA['products']:
        db.add(Product(**p))
    for c in DATA['coupons']:
        fields = {k: v for k, v in c.items() if k != 'note'}
        fields['starts_at'] = datetime.fromisoformat(fields['starts_at'])
        fields['ends_at'] = datetime.fromisoformat(fields['ends_at'])
        db.add(Coupon(**fields))
    settings = get_settings()
    admin_pw, demo_pw = settings.seed_admin_password, settings.seed_demo_password
    db.add(User(email='admin@example.com', password_hash=hash_password(admin_pw), name='管理員', role='admin'))
    db.add(User(email='demo@example.com', password_hash=hash_password(demo_pw), name='示範會員', role='member'))
    db.commit()
    print('示範資料建立完成：admin@example.com（管理員）、demo@example.com（會員）')


if __name__ == '__main__':
    if get_settings().env == 'production':
        raise SystemExit('正式環境禁止執行 seed')
    migrate()
    with SessionLocal() as session:
        seed(session)
