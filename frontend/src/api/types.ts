// API 資料型別的「好記名字」。真正的定義由 npm run gen:api 從 docs/api/openapi.yaml 產生（src/types/api.d.ts，勿手改）。
// 想知道某個欄位有沒有、叫什麼名字：看 docs/api/openapi.yaml。
import type { components } from '@/types/api'

type S = components['schemas']

export type User = S['UserOut']
export type Category = S['CategoryOut']
export type Product = S['ProductOut']
export type AdminProduct = S['AdminProductOut']
export type ProductCreate = S['ProductCreateIn']
export type ProductUpdate = S['ProductUpdateIn']
export type Cart = S['CartOut']
export type CartItem = S['CartItemOut']
export type Address = S['AddressOut']
export type AddressInput = S['AddressIn']
export type Quote = S['QuoteOut']
export type Order = S['OrderOut']
export type OrderSummary = S['OrderSummaryOut']
export type AdminOrder = S['AdminOrderOut']
export type OrderStatus = Order['status']
export type Payment = S['PaymentOut']
export type ProductSort = 'newest' | 'price_asc' | 'price_desc' | 'name'

/** 分頁結果（對應後端 Page[T]） */
export interface Page<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}
