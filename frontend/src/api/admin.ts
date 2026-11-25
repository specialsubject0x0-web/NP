// 後台 API（只有管理員能用；權限由後端檢查，前端隱藏按鈕不算數）。
import { request } from './client'
import type {
  AdminOrder,
  AdminProduct,
  Order,
  OrderStatus,
  Page,
  ProductCreate,
  ProductUpdate,
} from './types'

export const fetchAdminProducts = (page = 1, q?: string) =>
  request<Page<AdminProduct>>('GET', '/admin/products', { query: { page, page_size: 50, q } })
export const createProduct = (data: ProductCreate) =>
  request<AdminProduct>('POST', '/admin/products', { body: data })
export const updateProduct = (id: number, data: ProductUpdate) =>
  request<AdminProduct>('PATCH', `/admin/products/${id}`, { body: data })

export const fetchAdminOrders = (status?: OrderStatus, page = 1) =>
  request<Page<AdminOrder>>('GET', '/admin/orders', { query: { status, page, page_size: 20 } })
export const transitionOrder = (id: number, toStatus: 'shipped' | 'completed' | 'cancelled') =>
  request<Order>('POST', `/admin/orders/${id}/transition`, { body: { to_status: toStatus } })
