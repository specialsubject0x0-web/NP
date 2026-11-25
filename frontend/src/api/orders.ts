// 結帳、訂單、付款 API（需登入）。
// 【重要】金額一律由後端計算：fetchQuote 回傳的才是真正要付的錢，畫面上自己算的只供參考。
import { request } from './client'
import type { Order, OrderSummary, Page, Payment, Quote } from './types'

export const fetchQuote = (couponCode?: string) =>
  request<Quote>('POST', '/checkout/quote', { body: couponCode ? { coupon_code: couponCode } : {} })

export const createOrder = (addressId: number, couponCode: string | undefined, idempotencyKey: string) =>
  request<Order>('POST', '/orders', {
    body: couponCode ? { address_id: addressId, coupon_code: couponCode } : { address_id: addressId },
    headers: { 'Idempotency-Key': idempotencyKey },
  })

export const fetchOrders = (page = 1, pageSize = 10) =>
  request<Page<OrderSummary>>('GET', '/orders', { query: { page, page_size: pageSize } })
export const fetchOrder = (id: number) => request<Order>('GET', `/orders/${id}`)
export const cancelOrder = (id: number) => request<Order>('POST', `/orders/${id}/cancel`)
export const payOrder = (id: number, idempotencyKey: string) =>
  request<Payment>('POST', `/orders/${id}/payments`, { headers: { 'Idempotency-Key': idempotencyKey } })
