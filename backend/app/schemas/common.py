"""API 共用的輸入輸出格式。

【重要】所有「輸入」格式都繼承 StrictInput：多送任何欄位都會被拒絕（422），
例如有人想在下單時偷塞 price 或 total，後端會直接擋下（AGENTS.md 5.3「拒絕多餘欄位」）。
"""

from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field

# 資料庫 ID：必須是正整數，且不超過 32 位元整數上限
PositiveId = Annotated[int, Field(gt=0, le=2_147_483_647)]


class StrictInput(BaseModel):
    """前端送進來的資料：拒絕多餘欄位、自動去除字串前後空白。"""

    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)


class Output(BaseModel):
    """後端回傳的資料：可以直接從資料表物件轉換。"""

    model_config = ConfigDict(from_attributes=True)


class ErrorResponse(BaseModel):
    """統一錯誤格式。"""

    code: str = Field(examples=['ORDER_OUT_OF_STOCK'])
    message: str = Field(examples=['庫存不足'])
    details: dict[str, Any] = Field(default_factory=dict)


class Page[T](BaseModel):
    """分頁結果：items 是這一頁的資料，total 是全部有幾筆。"""

    items: list[T]
    total: int
    page: int
    page_size: int
