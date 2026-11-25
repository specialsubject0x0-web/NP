"""後端程式進入點：建立 FastAPI 應用程式、掛上所有 API、設定 CORS 與安全標頭。

啟動：在 backend/ 執行 `uv run uvicorn app.main:app --reload`，API 文件在 http://127.0.0.1:8000/docs（正式環境關閉）。
想新增 API：在 app/routers/ 新增檔案，然後在下方 include_router 加一行。
"""

from collections.abc import Awaitable, Callable

from fastapi import Depends, FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import Settings, get_settings
from app.core.deps import CSRF_HEADER, csrf_protect
from app.core.errors import register_error_handlers
from app.routers import admin, auth, cart, orders, products

API_PREFIX = '/api/v1'


def create_app(settings: Settings | None = None) -> FastAPI:
    """建立應用程式（測試時可以傳入不同設定）。"""
    settings = settings or get_settings()
    is_prod = settings.env == 'production'
    app = FastAPI(
        title='Shop API',
        version='1.0.0',
        description='購物網站 API 契約（前後端唯一介面）。金額單位：新台幣元（整數）。',
        docs_url=None if is_prod else '/docs',
        redoc_url=None,
        openapi_url=None if is_prod else '/openapi.json',
        # 【重要】所有 API 都先經過 CSRF 檢查（只檢查會改資料的請求）
        dependencies=[Depends(csrf_protect)],
    )
    register_error_handlers(app)

    # 【重要】CORS 白名單：只允許設定中的前端網址，且允許帶 Cookie（不可搭配 *）
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'],
        allow_headers=['Content-Type', CSRF_HEADER, 'Idempotency-Key'],
    )

    @app.middleware('http')
    async def security_headers(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """每個回應都加上安全標頭。"""
        response = await call_next(request)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'no-referrer'
        if request.url.path.startswith(API_PREFIX):
            # API 只回 JSON，不需要載入任何資源；也不要被瀏覽器或代理伺服器快取（可能含個人資料）
            response.headers['Content-Security-Policy'] = "default-src 'none'; frame-ancestors 'none'"
            response.headers['Cache-Control'] = 'no-store'
        return response

    for module in (auth, products, cart, orders, admin):
        app.include_router(module.router, prefix=API_PREFIX)

    @app.get(f'{API_PREFIX}/health', tags=['system'], summary='健康檢查')
    def health() -> dict[str, str]:
        return {'status': 'ok'}

    return app


app = create_app()
