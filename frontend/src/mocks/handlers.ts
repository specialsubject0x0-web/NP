// Mock 模式的 API 處理器（MSW）：攔截前端送出的 /api/v1/... 請求，用 db.ts 的假資料回應。
// 回應格式與 docs/api/openapi.yaml 相同，錯誤也用統一格式 { code, message, details }。
import { http, HttpResponse } from 'msw'
import type { AdminProduct, Cart, Order, Quote } from '@/api/types'
import { db, FREE_SHIPPING_THRESHOLD, SHIPPING_FEE } from './db'

const API = '*/api/v1'

function fail(status: number, code: string, message: string, details: Record<string, unknown> = {}) {
  return HttpResponse.json({ code, message, details }, { status })
}

function me() {
  return db.users.find((u) => u.id === db.currentUserId) ?? null
}

function publicUser() {
  const u = me()
  return u ? { id: u.id, email: u.email, name: u.name, role: u.role } : null
}

function cartOf(userId: number): Cart {
  const entries = Object.entries(db.carts[userId] ?? {})
  const items = entries.map(([pid, quantity]) => {
    const p = db.products.find((x) => x.id === Number(pid))!
    return {
      product_id: p.id,
      name: p.name,
      unit_price: p.price,
      quantity,
      line_total: p.price * quantity,
      stock: p.stock,
      image_color: p.image_color,
      is_available: p.is_active && p.stock >= quantity,
    }
  })
  return {
    items,
    item_count: items.reduce((s, i) => s + i.quantity, 0),
    subtotal: items.reduce((s, i) => s + i.line_total, 0),
    currency: 'TWD',
  }
}

/** 模仿後端的試算（見 db.ts 的說明）。回傳試算結果或錯誤回應。 */
function quoteFor(userId: number, email: string, code?: string): Quote | Response {
  const cart = cartOf(userId)
  if (cart.items.length === 0) return fail(409, 'CART_EMPTY', '購物車是空的')
  const bad = cart.items.find((i) => !i.is_available)
  if (bad)
    return fail(409, 'ORDER_OUT_OF_STOCK', `「${bad.name}」庫存不足或已下架`, { product_id: bad.product_id })
  let discount = 0
  let couponCode: string | null = null
  if (code) {
    const c = db.coupons.find((x) => x.code === code.toUpperCase())
    const now = new Date().toISOString()
    if (!c) return fail(422, 'COUPON_NOT_FOUND', '優惠碼無效')
    if (c.used.includes(email)) return fail(409, 'COUPON_ALREADY_USED', '你已經用過這張優惠券了')
    if (now >= c.ends_at) return fail(422, 'COUPON_EXPIRED', '這張優惠券已過期')
    if (cart.subtotal < c.min_spend)
      return fail(422, 'COUPON_MIN_SPEND_NOT_MET', `商品金額需滿 ${c.min_spend} 元才能使用`)
    discount = c.kind === 'percent' ? Math.floor((cart.subtotal * c.value) / 100) : c.value
    if (c.max_discount !== null) discount = Math.min(discount, c.max_discount)
    discount = Math.min(discount, cart.subtotal)
    couponCode = c.code
  }
  const shipping = cart.subtotal - discount >= FREE_SHIPPING_THRESHOLD ? 0 : SHIPPING_FEE
  return {
    items: cart.items.map((i) => ({
      product_id: i.product_id,
      name: i.name,
      unit_price: i.unit_price,
      quantity: i.quantity,
      line_total: i.line_total,
    })),
    subtotal: cart.subtotal,
    discount,
    shipping_fee: shipping,
    total: cart.subtotal - discount + shipping,
    currency: 'TWD',
    coupon_code: couponCode,
  }
}

function publicOrder(o: Order & { user_id?: number; idempotency_key?: string }): Order {
  const { user_id: _u, idempotency_key: _k, ...rest } = o
  return rest
}

const requireUser = () => (me() ? null : fail(401, 'AUTH_REQUIRED', '請先登入'))
const requireAdmin = () =>
  requireUser() ?? (me()?.role === 'admin' ? null : fail(403, 'FORBIDDEN', '沒有權限'))

export const handlers = [
  // ---- 會員 ----
  http.get(`${API}/auth/csrf`, () => HttpResponse.json({ csrf_token: 'mock-csrf-token' })),
  http.get(`${API}/auth/me`, () =>
    publicUser() ? HttpResponse.json(publicUser()) : fail(401, 'AUTH_REQUIRED', '請先登入'),
  ),
  http.post(`${API}/auth/login`, async ({ request }) => {
    const body = (await request.json()) as { email: string; password: string }
    const user = db.users.find((u) => u.email === body.email.toLowerCase() && u.password === body.password)
    if (!user) return fail(401, 'INVALID_CREDENTIALS', 'Email 或密碼錯誤')
    db.currentUserId = user.id
    return HttpResponse.json(publicUser())
  }),
  http.post(`${API}/auth/register`, async ({ request }) => {
    const body = (await request.json()) as { email: string; password: string; name: string }
    if (body.password.length < 8) return fail(422, 'VALIDATION_ERROR', '輸入資料格式不正確')
    if (db.users.some((u) => u.email === body.email.toLowerCase()))
      return fail(409, 'EMAIL_TAKEN', '這個 Email 已經註冊過了')
    const user = {
      id: db.nextId++,
      email: body.email.toLowerCase(),
      name: body.name,
      role: 'member' as const,
      password: body.password,
    }
    db.users.push(user)
    db.currentUserId = user.id
    return HttpResponse.json(publicUser(), { status: 201 })
  }),
  http.post(`${API}/auth/logout`, () => {
    db.currentUserId = null
    return new HttpResponse(null, { status: 204 })
  }),

  // ---- 商品 ----
  http.get(`${API}/categories`, () => HttpResponse.json(db.categories)),
  http.get(`${API}/products`, ({ request }) => {
    const p = new URL(request.url).searchParams
    const q = p.get('q') ?? ''
    const cat = p.get('category_id')
    const min = p.get('min_price')
    const max = p.get('max_price')
    if (min && max && Number(min) > Number(max))
      return fail(422, 'INVALID_PRICE_RANGE', '最低價格不能高於最高價格')
    let items = db.products.filter((x) => x.is_active)
    if (q) items = items.filter((x) => x.name.includes(q) || x.description.includes(q))
    if (cat) items = items.filter((x) => x.category_id === Number(cat))
    if (min) items = items.filter((x) => x.price >= Number(min))
    if (max) items = items.filter((x) => x.price <= Number(max))
    const sort = p.get('sort') ?? 'newest'
    const sorters: Record<string, (a: AdminProduct, b: AdminProduct) => number> = {
      newest: (a, b) => b.id - a.id,
      price_asc: (a, b) => a.price - b.price || a.id - b.id,
      price_desc: (a, b) => b.price - a.price || a.id - b.id,
      name: (a, b) => a.name.localeCompare(b.name),
    }
    if (!sorters[sort]) return fail(422, 'VALIDATION_ERROR', '輸入資料格式不正確')
    items = [...items].sort(sorters[sort])
    const page = Number(p.get('page') ?? 1)
    const size = Math.min(Number(p.get('page_size') ?? 12), 50)
    const slice = items.slice((page - 1) * size, page * size).map(({ is_active: _a, ...rest }) => rest)
    return HttpResponse.json({ items: slice, total: items.length, page, page_size: size })
  }),
  http.get(`${API}/products/:id`, ({ params }) => {
    const p = db.products.find((x) => x.id === Number(params.id) && x.is_active)
    if (!p) return fail(404, 'PRODUCT_NOT_FOUND', '找不到這個商品')
    const { is_active: _a, ...rest } = p
    return HttpResponse.json(rest)
  }),

  // ---- 購物車與地址 ----
  http.get(`${API}/cart`, () => requireUser() ?? HttpResponse.json(cartOf(me()!.id))),
  http.put(`${API}/cart/items/:id`, async ({ params, request }) => {
    const denied = requireUser()
    if (denied) return denied
    const { quantity } = (await request.json()) as { quantity: number }
    const p = db.products.find((x) => x.id === Number(params.id) && x.is_active)
    if (!p) return fail(404, 'PRODUCT_NOT_FOUND', '找不到這個商品')
    if (quantity < 1 || quantity > 99) return fail(422, 'VALIDATION_ERROR', '輸入資料格式不正確')
    if (quantity > p.stock)
      return fail(409, 'CART_EXCEEDS_STOCK', `庫存只剩 ${p.stock} 件`, { stock: p.stock })
    const uid = me()!.id
    db.carts[uid] = { ...db.carts[uid], [p.id]: quantity }
    return HttpResponse.json(cartOf(uid))
  }),
  http.delete(`${API}/cart/items/:id`, ({ params }) => {
    const denied = requireUser()
    if (denied) return denied
    const uid = me()!.id
    const cart = { ...db.carts[uid] }
    delete cart[Number(params.id)]
    db.carts[uid] = cart
    return HttpResponse.json(cartOf(uid))
  }),
  http.get(`${API}/addresses`, () => requireUser() ?? HttpResponse.json(db.addresses[me()!.id] ?? [])),
  http.post(`${API}/addresses`, async ({ request }) => {
    const denied = requireUser()
    if (denied) return denied
    const body = (await request.json()) as Record<string, string>
    if (!/^0\d{8,9}$/.test(body.phone ?? '') || !/^\d{3}(\d{2,3})?$/.test(body.postal_code ?? ''))
      return fail(422, 'VALIDATION_ERROR', '輸入資料格式不正確')
    const address = {
      id: db.nextId++,
      recipient: body.recipient!,
      phone: body.phone!,
      postal_code: body.postal_code!,
      city: body.city!,
      line: body.line!,
    }
    const uid = me()!.id
    db.addresses[uid] = [...(db.addresses[uid] ?? []), address]
    return HttpResponse.json(address, { status: 201 })
  }),
  http.delete(`${API}/addresses/:id`, ({ params }) => {
    const denied = requireUser()
    if (denied) return denied
    const uid = me()!.id
    db.addresses[uid] = (db.addresses[uid] ?? []).filter((a) => a.id !== Number(params.id))
    return new HttpResponse(null, { status: 204 })
  }),

  // ---- 結帳與訂單 ----
  http.post(`${API}/checkout/quote`, async ({ request }) => {
    const denied = requireUser()
    if (denied) return denied
    const body = (await request.json()) as { coupon_code?: string }
    const result = quoteFor(me()!.id, me()!.email, body.coupon_code)
    return result instanceof Response ? result : HttpResponse.json(result)
  }),
  http.post(`${API}/orders`, async ({ request }) => {
    const denied = requireUser()
    if (denied) return denied
    const user = me()!
    const key = request.headers.get('Idempotency-Key')
    if (!key || key.length < 8)
      return fail(400, 'IDEMPOTENCY_KEY_REQUIRED', '缺少或格式錯誤的 Idempotency-Key')
    const existing = db.orders.find((o) => o.user_id === user.id && o.idempotency_key === key)
    if (existing) return HttpResponse.json(publicOrder(existing))
    const body = (await request.json()) as { address_id: number; coupon_code?: string }
    const address = (db.addresses[user.id] ?? []).find((a) => a.id === body.address_id)
    if (!address) return fail(404, 'ADDRESS_NOT_FOUND', '找不到這個地址')
    const q = quoteFor(user.id, user.email, body.coupon_code)
    if (q instanceof Response) return q
    for (const line of q.items) db.products.find((p) => p.id === line.product_id)!.stock -= line.quantity
    if (q.coupon_code) db.coupons.find((c) => c.code === q.coupon_code)!.used.push(user.email)
    const order = {
      id: db.nextId++,
      user_id: user.id,
      idempotency_key: key,
      status: 'pending_payment' as const,
      subtotal: q.subtotal,
      discount: q.discount,
      shipping_fee: q.shipping_fee,
      total: q.total,
      currency: 'TWD',
      coupon_code: q.coupon_code,
      recipient_name: address.recipient,
      recipient_phone: address.phone,
      shipping_address: `${address.postal_code} ${address.city}${address.line}`,
      created_at: new Date().toISOString(),
      items: q.items.map((i) => ({
        product_id: i.product_id,
        product_name: i.name,
        unit_price: i.unit_price,
        quantity: i.quantity,
        line_total: i.line_total,
      })),
    }
    db.orders.push(order)
    db.carts[user.id] = {}
    return HttpResponse.json(publicOrder(order), { status: 201 })
  }),
  http.get(`${API}/orders`, () => {
    const denied = requireUser()
    if (denied) return denied
    const mine = db.orders.filter((o) => o.user_id === me()!.id).reverse()
    const items = mine.map((o) => ({
      id: o.id,
      status: o.status,
      total: o.total,
      currency: o.currency,
      created_at: o.created_at,
      item_count: o.items.reduce((s, i) => s + i.quantity, 0),
    }))
    return HttpResponse.json({ items, total: items.length, page: 1, page_size: 10 })
  }),
  http.get(`${API}/orders/:id`, ({ params }) => {
    const denied = requireUser()
    if (denied) return denied
    const o = db.orders.find((x) => x.id === Number(params.id) && x.user_id === me()!.id)
    return o ? HttpResponse.json(publicOrder(o)) : fail(404, 'ORDER_NOT_FOUND', '找不到這筆訂單')
  }),
  http.post(`${API}/orders/:id/cancel`, ({ params }) => {
    const denied = requireUser()
    if (denied) return denied
    const o = db.orders.find((x) => x.id === Number(params.id) && x.user_id === me()!.id)
    if (!o) return fail(404, 'ORDER_NOT_FOUND', '找不到這筆訂單')
    if (o.status !== 'pending_payment')
      return fail(409, 'ORDER_INVALID_TRANSITION', '訂單目前的狀態不能進行這個操作')
    o.status = 'cancelled'
    for (const i of o.items) db.products.find((p) => p.id === i.product_id)!.stock += i.quantity
    if (o.coupon_code) {
      const c = db.coupons.find((x) => x.code === o.coupon_code)!
      c.used = c.used.filter((e) => e !== me()!.email)
    }
    return HttpResponse.json(publicOrder(o))
  }),
  http.post(`${API}/orders/:id/payments`, ({ params }) => {
    const denied = requireUser()
    if (denied) return denied
    const o = db.orders.find((x) => x.id === Number(params.id) && x.user_id === me()!.id)
    if (!o) return fail(404, 'ORDER_NOT_FOUND', '找不到這筆訂單')
    if (o.status !== 'pending_payment')
      return fail(409, 'ORDER_INVALID_TRANSITION', '訂單目前的狀態不能進行這個操作')
    o.status = 'paid'
    return HttpResponse.json({ transaction_id: `MOCK-${o.id}`, status: 'succeeded', order_status: 'paid' })
  }),

  // ---- 後台 ----
  http.get(
    `${API}/admin/products`,
    () =>
      requireAdmin() ??
      HttpResponse.json({ items: db.products, total: db.products.length, page: 1, page_size: 50 }),
  ),
  http.post(`${API}/admin/products`, async ({ request }) => {
    const denied = requireAdmin()
    if (denied) return denied
    const body = (await request.json()) as Omit<AdminProduct, 'id' | 'currency'>
    const product = { ...body, id: db.nextId++, currency: 'TWD', description: body.description ?? '' }
    db.products.push(product)
    return HttpResponse.json(product, { status: 201 })
  }),
  http.patch(`${API}/admin/products/:id`, async ({ params, request }) => {
    const denied = requireAdmin()
    if (denied) return denied
    const p = db.products.find((x) => x.id === Number(params.id))
    if (!p) return fail(404, 'PRODUCT_NOT_FOUND', '找不到這個商品')
    const body = (await request.json()) as Partial<AdminProduct>
    if ((body.price ?? 0) < 0 || (body.stock ?? 0) < 0)
      return fail(422, 'VALIDATION_ERROR', '輸入資料格式不正確')
    Object.assign(p, body)
    return HttpResponse.json(p)
  }),
  http.get(`${API}/admin/orders`, ({ request }) => {
    const denied = requireAdmin()
    if (denied) return denied
    const status = new URL(request.url).searchParams.get('status')
    const list = db.orders.filter((o) => !status || o.status === status).reverse()
    const items = list.map((o) => ({
      id: o.id,
      status: o.status,
      total: o.total,
      currency: o.currency,
      created_at: o.created_at,
      item_count: o.items.reduce((s, i) => s + i.quantity, 0),
      user_id: o.user_id,
      recipient_name: o.recipient_name,
    }))
    return HttpResponse.json({ items, total: items.length, page: 1, page_size: 20 })
  }),
  http.post(`${API}/admin/orders/:id/transition`, async ({ params, request }) => {
    const denied = requireAdmin()
    if (denied) return denied
    const o = db.orders.find((x) => x.id === Number(params.id))
    if (!o) return fail(404, 'ORDER_NOT_FOUND', '找不到這筆訂單')
    const { to_status } = (await request.json()) as { to_status: Order['status'] }
    const allowed: Record<string, string[]> = {
      pending_payment: ['cancelled'],
      paid: ['shipped'],
      shipped: ['completed'],
    }
    if (!allowed[o.status]?.includes(to_status))
      return fail(409, 'ORDER_INVALID_TRANSITION', '訂單目前的狀態不能進行這個操作')
    if (to_status === 'cancelled')
      for (const i of o.items) db.products.find((p) => p.id === i.product_id)!.stock += i.quantity
    o.status = to_status
    return HttpResponse.json(publicOrder(o))
  }),
]
