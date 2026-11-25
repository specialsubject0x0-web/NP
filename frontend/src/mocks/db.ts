// Mock 模式的「假資料庫」：資料存在瀏覽器記憶體，重新整理頁面就會回到初始狀態。
// 商品資料複製自 backend/scripts/seed_data.json（兩邊顯示相同的示範商品）。
// 【重要】這裡的運費、優惠券計算只是「模仿」後端，讓 Mock 模式能展示；真正的規則在後端 pricing_service.py。
//         後端規則改了，這裡要跟著改（或接受 Mock 與真實不同）。
import seed from './seed-data.json'
import type { Address, AdminProduct, Category, Order, User } from '@/api/types'

interface MockUser extends User {
  password: string
}
interface MockCoupon {
  code: string
  kind: string
  value: number
  max_discount: number | null
  min_spend: number
  starts_at: string
  ends_at: string
  usage_limit: number | null
  used: string[] // 用過的會員 email
}
interface MockOrder extends Order {
  user_id: number
  idempotency_key: string
}

export interface MockDb {
  users: MockUser[]
  currentUserId: number | null
  categories: Category[]
  products: AdminProduct[]
  carts: Record<number, Record<number, number>> // userId → { productId: 數量 }
  addresses: Record<number, Address[]>
  orders: MockOrder[]
  coupons: MockCoupon[]
  nextId: number
}

export function createDb(): MockDb {
  return {
    users: [
      { id: 1, email: 'admin@example.com', name: '管理員', role: 'admin', password: 'admin12345' },
      { id: 2, email: 'demo@example.com', name: '示範會員', role: 'member', password: 'demo12345' },
    ],
    currentUserId: null,
    categories: seed.categories,
    products: seed.products.map((p) => ({ ...p, currency: 'TWD', is_active: true })),
    carts: {},
    addresses: {},
    orders: [],
    coupons: seed.coupons.map((c) => ({ ...c, used: [] })),
    nextId: 100,
  }
}

export let db = createDb()

/** 測試用：把假資料庫恢復成初始狀態。 */
export function resetDb(): void {
  db = createDb()
}

export const SHIPPING_FEE = 60
export const FREE_SHIPPING_THRESHOLD = 1000
