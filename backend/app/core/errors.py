"""統一的錯誤格式：{ "code": "ORDER_OUT_OF_STOCK", "message": "庫存不足", "details": {} }。

誰會用到：service 遇到不合規則的情況就 raise AppError(...)，這裡負責轉成 JSON 回應。
【重要】對外只回「通用訊息」，不回傳程式堆疊或資料庫錯誤細節（避免洩露內部資訊）。
"""

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger('shop')


class AppError(Exception):
    """商業規則錯誤。status_code 是 HTTP 狀態碼；code 是給前端判斷用的英文代碼；message 給人看。"""

    def __init__(self, status_code: int, code: str, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or {}


def error_body(code: str, message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    """組出統一格式的錯誤 JSON。"""
    return {'code': code, 'message': message, 'details': details or {}}


_HTTP_CODES = {
    401: ('AUTH_REQUIRED', '請先登入'),
    403: ('FORBIDDEN', '沒有權限'),
    404: ('NOT_FOUND', '找不到資源'),
    405: ('METHOD_NOT_ALLOWED', '不支援的請求方法'),
}


def register_error_handlers(app: FastAPI) -> None:
    """把各種錯誤都轉成統一格式。"""

    @app.exception_handler(AppError)
    async def _app_error(_req: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content=error_body(exc.code, exc.message, exc.details))

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_req: Request, exc: RequestValidationError) -> JSONResponse:
        # 【為什麼】只回欄位位置與錯誤類型，不把使用者送來的原始值回傳（避免反射攻擊與洩露）
        fields = [{'loc': [str(p) for p in err.get('loc', ())], 'type': err.get('type', '')} for err in exc.errors()]
        return JSONResponse(status_code=422, content=error_body('VALIDATION_ERROR', '輸入資料格式不正確', {'fields': fields}))

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(_req: Request, exc: StarletteHTTPException) -> JSONResponse:
        code, message = _HTTP_CODES.get(exc.status_code, ('HTTP_ERROR', '請求失敗'))
        return JSONResponse(status_code=exc.status_code, content=error_body(code, message))

    @app.exception_handler(Exception)
    async def _unexpected(_req: Request, exc: Exception) -> JSONResponse:
        # 詳細錯誤只寫進伺服器 log，回給使用者的只有通用訊息
        logger.exception('未預期的錯誤：%s', type(exc).__name__)
        return JSONResponse(status_code=500, content=error_body('INTERNAL_ERROR', '系統發生錯誤，請稍後再試'))
