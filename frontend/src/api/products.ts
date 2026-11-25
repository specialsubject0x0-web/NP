// 商品與分類 API（不需登入）。
import { request } from './client'
import type { Category, Page, Product, ProductSort } from './types'

export interface ProductQuery {
  q?: string
  category_id?: number
  min_price?: number
  max_price?: number
  sort?: ProductSort
  page?: number
  page_size?: number
}

export const fetchProducts = (query: ProductQuery = {}) =>
  request<Page<Product>>('GET', '/products', { query: { ...query } })
export const fetchProduct = (id: number) => request<Product>('GET', `/products/${id}`)
export const fetchCategories = () => request<Category[]>('GET', '/categories')
