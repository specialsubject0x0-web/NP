"""站台設定：從環境變數或 .env 讀取。

誰會用到：資料庫連線、Cookie、CORS、金流簽章都從這裡拿設定。
想修改時：不要改這個檔案的預設值，請在 backend/.env 設定（參考 .env.example）。
【重要】機密（例如金流簽章金鑰）只能放 .env，不得寫進程式碼或 commit 進 git。
"""

from functools import lru_cache
from typing import Literal, Self

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# 開發用的預設金鑰；正式環境若還在用它，程式會拒絕啟動（見下方檢查）
DEV_ONLY_SECRET = 'dev-only-change-me'  # noqa: S105 - 公開的開發佔位值，正式環境會被拒絕


class Settings(BaseSettings):
    """所有設定。環境變數名稱 = SHOP_ + 欄位大寫，例如 SHOP_DATABASE_URL。"""

    model_config = SettingsConfigDict(env_file='.env', env_prefix='SHOP_', extra='ignore')

    env: Literal['development', 'test', 'production'] = 'development'
    database_url: str = 'sqlite:///./shop.db'
    # 【重要】只允許這些前端網址跨網域呼叫 API（CORS 白名單），不可以設成 *
    cors_origins: list[str] = ['http://localhost:5173', 'http://127.0.0.1:5173']
    session_days: int = 7
    payment_webhook_secret: str = DEV_ONLY_SECRET
    # 示範帳號密碼：只有 scripts/seed.py 會用到（正式環境禁止執行 seed）
    seed_admin_password: str = 'admin12345'  # noqa: S105 - 公開的示範密碼
    seed_demo_password: str = 'demo12345'  # noqa: S105 - 公開的示範密碼

    @property
    def cookie_secure(self) -> bool:
        """正式環境的 Cookie 只能走 HTTPS（Secure）。本機開發是 http，所以關掉。"""
        return self.env == 'production'

    @model_validator(mode='after')
    def _check_production(self) -> Self:
        # 【為什麼】避免忘記換金鑰就上線：任何人都能偽造付款回呼
        if self.env == 'production' and self.payment_webhook_secret == DEV_ONLY_SECRET:
            raise ValueError('正式環境必須設定 SHOP_PAYMENT_WEBHOOK_SECRET')
        if '*' in self.cors_origins:
            raise ValueError('CORS 白名單不可以使用 *')
        return self


@lru_cache
def get_settings() -> Settings:
    """取得設定（只讀一次，之後重複使用）。"""
    return Settings()
