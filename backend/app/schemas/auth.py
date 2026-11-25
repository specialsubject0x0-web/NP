"""註冊、登入相關的格式。【重要】UserOut 沒有 password_hash，回應中絕不出現密碼雜湊。"""

from typing import Literal

from pydantic import Field

from app.schemas.common import Output, StrictInput

EMAIL_PATTERN = r'^[^@\s]+@[^@\s]+\.[^@\s]+$'


class RegisterIn(StrictInput):
    """註冊：Email、密碼（至少 8 字，R-16）、顯示名稱。"""

    email: str = Field(max_length=254, pattern=EMAIL_PATTERN)
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=1, max_length=50)


class LoginIn(StrictInput):
    """登入：Email 與密碼。"""

    email: str = Field(max_length=254)
    password: str = Field(min_length=1, max_length=128)


class UserOut(Output):
    """目前登入者的公開資料。"""

    id: int
    email: str
    name: str
    role: Literal['member', 'admin']


class CsrfOut(Output):
    """CSRF token（前端放在 X-CSRF-Token 標頭）。"""

    csrf_token: str
