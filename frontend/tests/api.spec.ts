// src/api/client.ts：CSRF、錯誤格式、網路錯誤、Idempotency-Key。
import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'
import { ApiError, newIdempotencyKey, request } from '@/api/client'
import { fetchProducts } from '@/api/products'
import { createOrder } from '@/api/orders'
import { server } from './setup'

describe('api client', () => {
  it('會改資料的請求會帶 CSRF token', async () => {
    let seen: string | null = null
    server.use(
      http.post('*/api/v1/auth/logout', ({ request: req }) => {
        seen = req.headers.get('X-CSRF-Token')
        return new HttpResponse(null, { status: 204 })
      }),
    )
    await expect(request('POST', '/auth/logout')).resolves.toBeUndefined()
    expect(seen).toBe('mock-csrf-token')
  })

  it('把後端錯誤轉成 ApiError（含 code 與 message）', async () => {
    const err = await request('GET', '/products/999').catch((e: unknown) => e)
    expect(err).toBeInstanceOf(ApiError)
    expect(err).toMatchObject({ status: 404, code: 'PRODUCT_NOT_FOUND', message: '找不到這個商品' })
  })

  it('回應不是 JSON 時給通用訊息', async () => {
    server.use(http.get('*/api/v1/categories', () => new HttpResponse('oops', { status: 500 })))
    await expect(request('GET', '/categories')).rejects.toMatchObject({
      code: 'HTTP_ERROR',
      message: '請求失敗',
    })
  })

  it('網路斷線時給中文提示', async () => {
    server.use(http.get('*/api/v1/categories', () => HttpResponse.error()))
    await expect(request('GET', '/categories')).rejects.toMatchObject({ code: 'NETWORK_ERROR' })
  })

  it('查詢參數會略過空值', async () => {
    let url = ''
    server.use(
      http.get('*/api/v1/products', ({ request: req }) => {
        url = req.url
        return HttpResponse.json({ items: [], total: 0, page: 1, page_size: 12 })
      }),
    )
    await fetchProducts({ q: '', sort: 'price_asc', category_id: undefined })
    expect(url).toContain('sort=price_asc')
    expect(url).not.toContain('q=')
    expect(url).not.toContain('category_id')
  })

  it('建立訂單會帶 Idempotency-Key，且每次產生的 key 都不同', async () => {
    let key: string | null = null
    server.use(
      http.post('*/api/v1/orders', ({ request: req }) => {
        key = req.headers.get('Idempotency-Key')
        return HttpResponse.json({}, { status: 201 })
      }),
    )
    const k = newIdempotencyKey()
    await createOrder(1, undefined, k)
    expect(key).toBe(k)
    expect(newIdempotencyKey()).not.toBe(k)
  })
})
