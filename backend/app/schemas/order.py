"""結帳試算、訂單、付款的格式。"""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import Field

from app.schemas.common import Output, PositiveId, StrictInput

OrderStatus = Literal['pending_payment', 'paid', 'shipped', 'completed', 'cancelled']
# 優惠碼只能是英數、底線、連字號；只能填一個（R-12 不可疊加）
CouponCode = Annotated[str, Field(min_length=1, max_length=32, pattern=r'^[A-Za-z0-9_-]+$')]


class QuoteIn(StrictInput):
    """結帳試算：可選擇帶一張優惠碼。"""

    coupon_code: CouponCode | None = None


class QuoteLineOut(Output):
    product_id: int
    name: str
    unit_price: int
    quantity: int
    line_total: int


class QuoteOut(Output):
    """後端計算的金額（真相來源）。total = subtotal - discount + shipping_fee。"""

    items: list[QuoteLineOut]
    subtotal: int
    discount: int
    shipping_fee: int
    total: int
    currency: str
    coupon_code: str | None


class OrderCreateIn(StrictInput):
    """建立訂單：選地址、可帶優惠碼。注意：沒有價格欄位，金額一律由後端計算。"""

    address_id: PositiveId
    coupon_code: CouponCode | None = None


class OrderItemOut(Output):
    product_id: int
    product_name: str
    unit_price: int
    quantity: int
    line_total: int


class OrderOut(Output):
    id: int
    status: OrderStatus
    subtotal: int
    discount: int
    shipping_fee: int
    total: int
    currency: str
    coupon_code: str | None
    recipient_name: str
    recipient_phone: str
    shipping_address: str
    created_at: datetime
    items: list[OrderItemOut]


class OrderSummaryOut(Output):
    """訂單列表用的精簡資料。"""

    id: int
    status: OrderStatus
    total: int
    currency: str
    created_at: datetime
    item_count: int


class AdminOrderOut(OrderSummaryOut):
    user_id: int
    recipient_name: str


class TransitionIn(StrictInput):
    """後台改訂單狀態。paid 只能由付款回呼產生，所以這裡不能選。"""

    to_status: Literal['shipped', 'completed', 'cancelled']


class PaymentOut(Output):
    transaction_id: str
    status: Literal['pending', 'succeeded', 'failed']
    order_status: OrderStatus


class PaymentCallbackIn(StrictInput):
    """金流回呼內容。簽章放在 X-Signature 標頭（R-10）。"""

    transaction_id: str = Field(min_length=1, max_length=64)
    order_id: PositiveId
    amount: int = Field(ge=0)
    status: Literal['succeeded', 'failed']


class PaymentCallbackOut(Output):
    received: bool
    payment_status: Literal['pending', 'succeeded', 'failed']
