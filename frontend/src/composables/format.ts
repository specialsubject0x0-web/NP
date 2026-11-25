// 顯示用的格式化小工具：金額、時間、訂單狀態的中文名稱。
import { siteConfig } from '@/config/site.config'
import type { OrderStatus } from '@/api/types'

/** 金額顯示：1234 → 「NT$1,234」。後端傳來的是整數元。 */
export function formatPrice(amount: number): string {
  return `NT$${amount.toLocaleString(siteConfig.locale)}`
}

/** 時間顯示：把後端的 UTC 時間轉成台灣時間。 */
export function formatDate(iso: string): string {
  return new Date(iso).toLocaleString(siteConfig.locale, {
    timeZone: siteConfig.timeZone,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  })
}

// 【可修改】訂單狀態顯示的中文名稱
export const STATUS_LABELS: Record<OrderStatus, string> = {
  pending_payment: '待付款',
  paid: '已付款',
  shipped: '已出貨',
  completed: '已完成',
  cancelled: '已取消',
}
