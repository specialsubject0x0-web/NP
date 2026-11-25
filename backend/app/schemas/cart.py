"""購物車與地址的格式。"""

from pydantic import Field

from app.core import business_rules as rules
from app.schemas.common import Output, StrictInput


class CartItemIn(StrictInput):
    """設定某商品在購物車的數量（1–99，R-05）。"""

    quantity: int = Field(ge=1, le=rules.CART_MAX_QUANTITY)


class CartItemOut(Output):
    product_id: int
    name: str
    unit_price: int
    quantity: int
    line_total: int
    stock: int
    image_color: str
    is_available: bool  # 商品下架或庫存不足時為 False，前端提示使用者


class CartOut(Output):
    """購物車。subtotal 只供顯示；真正要付的金額以結帳試算為準（AGENTS.md 6.3）。"""

    items: list[CartItemOut]
    item_count: int
    subtotal: int
    currency: str


class AddressIn(StrictInput):
    """新增收件地址。電話：台灣手機 09 開頭 10 碼，或市話（含區碼）9–10 碼。"""

    recipient: str = Field(min_length=1, max_length=50)
    phone: str = Field(pattern=r'^0\d{8,9}$')
    postal_code: str = Field(pattern=r'^\d{3}(\d{2,3})?$')
    city: str = Field(min_length=1, max_length=20)
    line: str = Field(min_length=1, max_length=200)


class AddressOut(Output):
    id: int
    recipient: str
    phone: str
    postal_code: str
    city: str
    line: str
