"""會員 API：/api/v1/auth/...（US-008）。router 只處理 HTTP（Cookie、狀態碼），規則在 auth_service。"""

from fastapi import APIRouter, Request, Response

from app.core.config import get_settings
from app.core.deps import CSRF_COOKIE, DB, SESSION_COOKIE, CurrentUser
from app.core.security import new_token
from app.schemas.auth import CsrfOut, LoginIn, RegisterIn, UserOut
from app.schemas.common import ErrorResponse
from app.services import auth_service
from app.services.auth_service import LoginResult

router = APIRouter(prefix='/auth', tags=['auth'])


def _set_cookies(response: Response, session_token: str | None, csrf_token: str) -> None:
    """設定 Cookie。session 是 httpOnly（JavaScript 讀不到，XSS 偷不走）；csrf 必須讓前端讀得到。"""
    settings = get_settings()
    max_age = settings.session_days * 86400
    if session_token is not None:
        response.set_cookie(
            SESSION_COOKIE, session_token, max_age=max_age, httponly=True, secure=settings.cookie_secure, samesite='lax', path='/'
        )
    response.set_cookie(CSRF_COOKIE, csrf_token, max_age=max_age, httponly=False, secure=settings.cookie_secure, samesite='lax', path='/')


def _login_response(response: Response, result: LoginResult) -> UserOut:
    _set_cookies(response, result.session_token, result.csrf_token)
    return UserOut.model_validate(result.user)


@router.get('/csrf', response_model=CsrfOut, summary='取得 CSRF token（網站開啟時先呼叫一次）')
def get_csrf(request: Request, response: Response) -> CsrfOut:
    token = request.cookies.get(CSRF_COOKIE) or new_token()
    _set_cookies(response, None, token)
    return CsrfOut(csrf_token=token)


@router.post('/register', response_model=UserOut, status_code=201, responses={409: {'model': ErrorResponse}}, summary='註冊並登入')
def register(data: RegisterIn, response: Response, db: DB) -> UserOut:
    return _login_response(response, auth_service.register(db, data))


@router.post('/login', response_model=UserOut, responses={401: {'model': ErrorResponse}, 429: {'model': ErrorResponse}}, summary='登入')
def login(data: LoginIn, request: Request, response: Response, db: DB) -> UserOut:
    client_ip = request.client.host if request.client else 'unknown'
    return _login_response(response, auth_service.login(db, data, client_ip))


@router.post('/logout', status_code=204, summary='登出')
def logout(request: Request, db: DB) -> Response:
    auth_service.logout(db, request.cookies.get(SESSION_COOKIE))
    response = Response(status_code=204)
    response.delete_cookie(SESSION_COOKIE, path='/')
    return response


@router.get('/me', response_model=UserOut, responses={401: {'model': ErrorResponse}}, summary='目前登入者')
def me(user: CurrentUser) -> UserOut:
    return UserOut.model_validate(user)
