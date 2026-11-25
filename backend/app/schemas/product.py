"""商品與分類的格式。"""

from typing import Literal

from pydantic import Field

from app.core import business_rules as rules
from app.schemas.common import Output, PositiveId, StrictInput

SortOption = Literal['newest', 'price_asc', 'price_desc', 'name']  # R-18 排序白名單
COLOR_PATTERN = r'^#[0-9a-fA-F]{6}$'


class CategoryOut(Output):
    id: int
    name: str
    slug: str


class ProductOut(Output):
    """前台看到的商品資料。price 為整數元（R-01）。"""

    id: int
    name: str
    description: str
    price: int
    currency: str
    stock: int
    image_color: str
    category_id: int


class AdminProductOut(ProductOut):
    """後台看到的商品資料（多了是否上架）。"""

    is_active: bool


class ProductCreateIn(StrictInput):
    """後台新增商品。價格與庫存不可為負數。"""

    name: str = Field(min_length=1, max_length=100)
    description: str = Field(default='', max_length=2000)
    price: int = Field(ge=0, le=10_000_000)
    stock: int = Field(ge=0, le=1_000_000)
    category_id: PositiveId
    image_color: str = Field(default='#94a3b8', pattern=COLOR_PATTERN)
    is_active: bool = True


class ProductUpdateIn(StrictInput):
    """後台修改商品：只送要改的欄位即可。"""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=2000)
    price: int | None = Field(default=None, ge=0, le=10_000_000)
    stock: int | None = Field(default=None, ge=0, le=1_000_000)
    category_id: PositiveId | None = None
    image_color: str | None = Field(default=None, pattern=COLOR_PATTERN)
    is_active: bool | None = None


class ProductQuery(StrictInput):
    """商品列表查詢條件。page_size 上限 50（R-18）。"""

    q: str | None = Field(default=None, max_length=50)
    category_id: PositiveId | None = None
    min_price: int | None = Field(default=None, ge=0)
    max_price: int | None = Field(default=None, ge=0)
    sort: SortOption = 'newest'
    page: int = Field(default=1, ge=1, le=10_000)
    page_size: int = Field(default=12, ge=1, le=rules.PAGE_SIZE_MAX)
