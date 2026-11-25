"""結帳、訂單、付款 API（US-005、US-006、US-007、US-011）。"""

from typing import Annotated

from fastapi import APIRouter, Header, Path, Query, Response

from app.core import business_rules as rules
from app.core.deps import DB, CurrentUser, IdempotencyKey, RateLimitedUser
from app.models import Order
from app.schemas.common import ErrorResponse, Page
from app.schemas.order import (
    OrderCreateIn,
    OrderOut,
    OrderSummaryOut,
    PaymentCallbackIn,
    PaymentCallbackOut,
    PaymentOut,
    QuoteIn,
    QuoteLineOut,
    QuoteOut,
)
from app.services import order_service, payment_service, pricing_service

router = APIRouter(tags=['orders'])
IdPath = Annotated[int, Path(gt=0, le=2_147_483_647)]
_errors: dict[int | str, dict[str, object]] = {s: {'model': ErrorResponse} for s in (400, 401, 403, 404, 409, 422, 429)}


def summary(order: Order) -> OrderSummaryOut:
    return OrderSummaryOut(
        id=order.id,
        status=order.status,
        total=order.total,
        currency=order.currency,
        created_at=order.created_at,
        item_count=sum(i.quantity for i in order.items),
    )


@router.post('/checkout/quote', response_model=QuoteOut, responses=_errors, summary='結帳試算（後端計算金額）')
def quote(data: QuoteIn, user: RateLimitedUser, db: DB) -> QuoteOut:
    q = pricing_service.build_quote(db, user, data.coupon_code)
    return QuoteOut(
        items=[QuoteLineOut(**line.__dict__) for line in q.lines],
        subtotal=q.subtotal,
        discount=q.discount,
        shipping_fee=q.shipping_fee,
        total=q.total,
        currency=q.currency,
        coupon_code=q.coupon_code,
    )


@router.post('/orders', response_model=OrderOut, status_code=201, responses=_errors, summary='建立訂單（需 Idempotency-Key）')
def create_order(data: OrderCreateIn, key: IdempotencyKey, user: RateLimitedUser, db: DB, response: Response) -> OrderOut:
    order, created = order_service.create_order(db, user, data.address_id, data.coupon_code, key)
    if not created:
        response.status_code = 200  # 重複請求：回傳第一次建立的訂單
    return OrderOut.model_validate(order)


@router.get('/orders', response_model=Page[OrderSummaryOut], responses=_errors, summary='我的訂單')
def list_orders(
    user: CurrentUser,
    db: DB,
    page: Annotated[int, Query(ge=1, le=10_000)] = 1,
    page_size: Annotated[int, Query(ge=1, le=rules.PAGE_SIZE_MAX)] = 10,
) -> Page[OrderSummaryOut]:
    items, total = order_service.list_user_orders(db, user, page, page_size)
    return Page[OrderSummaryOut](items=[summary(o) for o in items], total=total, page=page, page_size=page_size)


@router.get('/orders/{order_id}', response_model=OrderOut, responses=_errors, summary='訂單詳情')
def get_order(order_id: IdPath, user: CurrentUser, db: DB) -> OrderOut:
    return OrderOut.model_validate(order_service.get_user_order(db, user, order_id))


@router.post('/orders/{order_id}/cancel', response_model=OrderOut, responses=_errors, summary='取消待付款訂單')
def cancel_order(order_id: IdPath, user: CurrentUser, db: DB) -> OrderOut:
    return OrderOut.model_validate(order_service.cancel_by_user(db, user, order_id))


@router.post('/orders/{order_id}/payments', response_model=PaymentOut, responses=_errors, summary='付款（模擬金流，需 Idempotency-Key）')
def pay_order(order_id: IdPath, key: IdempotencyKey, user: CurrentUser, db: DB) -> PaymentOut:
    payment, order = payment_service.start_payment(db, user, order_id, key)
    return PaymentOut(transaction_id=payment.transaction_id, status=payment.status, order_status=order.status)


@router.post('/payments/callback', response_model=PaymentCallbackOut, responses=_errors, summary='金流回呼（需 X-Signature 簽章）')
def payment_callback(
    data: PaymentCallbackIn, db: DB, signature: Annotated[str | None, Header(alias='X-Signature')] = None
) -> PaymentCallbackOut:
    payment = payment_service.handle_callback(db, data, signature)
    return PaymentCallbackOut(received=True, payment_status=payment.status)
