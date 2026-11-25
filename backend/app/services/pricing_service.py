"""金額計算（結帳試算、優惠券、運費）。

【重要】這是全站「唯一」計算金額的地方（AGENTS.md 6.3：折扣邏輯集中在後端一個 service）。
前端顯示的任何金額都只是參考；下單時一定重新呼叫這裡計算。
改這個檔案前請先讀 docs/regulations/business-rules.md 的 R-03、R-12，並跑 tests/test_pricing.py。
"""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from app.core import business_rules as rules
from app.core.errors import AppError
from app.models import Coupon, User
from app.models.base import utcnow
from app.repositories import cart_repo, order_repo


@dataclass(frozen=True)
class QuoteLine:
    product_id: int
    name: str
    unit_price: int
    quantity: int
    line_total: int


@dataclass(frozen=True)
class Quote:
    """試算結果。total = subtotal - discount + shipping_fee。"""

    lines: list[QuoteLine]
    subtotal: int
    discount: int
    shipping_fee: int
    total: int
    currency: str
    coupon: Coupon | None

    @property
    def coupon_code(self) -> str | None:
        return self.coupon.code if self.coupon else None


def shipping_fee_for(amount_after_discount: int) -> int:
    """運費（R-03）：折扣後金額達門檻免運，否則收固定運費。"""
    return 0 if amount_after_discount >= rules.FREE_SHIPPING_THRESHOLD else rules.SHIPPING_FEE


def coupon_discount(coupon: Coupon, subtotal: int, now: datetime) -> int:
    """依優惠券規則算出折扣金額；不符合規則就 raise AppError（R-12）。

    檢查順序：是否啟用 → 是否在有效期間 → 是否達最低消費 → 是否還有總次數。
    """
    if not coupon.is_active:
        raise AppError(422, 'COUPON_NOT_FOUND', '優惠碼無效')
    if now < coupon.starts_at:
        raise AppError(422, 'COUPON_NOT_STARTED', '這張優惠券還沒開始')
    if now >= coupon.ends_at:
        raise AppError(422, 'COUPON_EXPIRED', '這張優惠券已過期')
    if subtotal < coupon.min_spend:
        raise AppError(422, 'COUPON_MIN_SPEND_NOT_MET', f'商品金額需滿 {coupon.min_spend} 元才能使用', {'min_spend': coupon.min_spend})
    if coupon.usage_limit is not None and coupon.used_count >= coupon.usage_limit:
        raise AppError(409, 'COUPON_USAGE_LIMIT_REACHED', '這張優惠券已經被用完了')

    if coupon.kind == 'percent':
        # 【為什麼】用整數運算並無條件捨去（//），避免小數誤差；再套用單筆上限 max_discount
        percent = min(coupon.value, rules.PERCENT_COUPON_MAX)
        discount = subtotal * percent // 100
        if coupon.max_discount is not None:
            discount = min(discount, coupon.max_discount)
    else:
        discount = coupon.value
    # 折扣不能超過商品小計（不會變成負數，也不折運費）
    return min(discount, subtotal)


def build_quote(db: Session, user: User, coupon_code: str | None) -> Quote:
    """用「現在資料庫中的價格與庫存」計算這位會員購物車的應付金額。"""
    items = cart_repo.list_items(db, user.id)
    if not items:
        raise AppError(409, 'CART_EMPTY', '購物車是空的')
    lines: list[QuoteLine] = []
    for item in items:
        product = item.product
        if not product.is_active or product.stock < item.quantity:
            raise AppError(
                409,
                'ORDER_OUT_OF_STOCK',
                f'「{product.name}」庫存不足或已下架',
                {'product_id': product.id, 'stock': product.stock if product.is_active else 0},
            )
        lines.append(QuoteLine(product.id, product.name, product.price, item.quantity, product.price * item.quantity))
    subtotal = sum(line.line_total for line in lines)

    coupon: Coupon | None = None
    discount = 0
    if coupon_code:
        coupon = order_repo.get_coupon(db, coupon_code)
        if coupon is None:
            raise AppError(422, 'COUPON_NOT_FOUND', '優惠碼無效')
        if order_repo.has_redeemed(db, coupon.id, user.id):
            raise AppError(409, 'COUPON_ALREADY_USED', '你已經用過這張優惠券了')
        discount = coupon_discount(coupon, subtotal, utcnow())

    shipping = shipping_fee_for(subtotal - discount)
    return Quote(lines, subtotal, discount, shipping, subtotal - discount + shipping, rules.CURRENCY, coupon)
