// 頁面測試：用和 Mock 模式相同的假後端，模擬使用者操作主要流程。
import { describe, expect, it, vi } from 'vitest'
import App from '@/App.vue'
import { db } from '@/mocks/db'
import CartView from '@/views/CartView.vue'
import CheckoutView from '@/views/CheckoutView.vue'
import FaqView from '@/views/FaqView.vue'
import HomeView from '@/views/HomeView.vue'
import LoginView from '@/views/LoginView.vue'
import NotFoundView from '@/views/NotFoundView.vue'
import OrderDetailView from '@/views/OrderDetailView.vue'
import OrderListView from '@/views/OrderListView.vue'
import ProductDetailView from '@/views/ProductDetailView.vue'
import ProductListView from '@/views/ProductListView.vue'
import RegisterView from '@/views/RegisterView.vue'
import AdminOrdersView from '@/views/admin/AdminOrdersView.vue'
import AdminProductsView from '@/views/admin/AdminProductsView.vue'
import { mountWithApp, settle } from './helpers'

function loginAs(id: number): void {
  db.currentUserId = id
}

describe('首頁與商品', () => {
  it('首頁顯示文案、分類與精選商品', async () => {
    const { wrapper } = await mountWithApp(HomeView)
    expect(wrapper.text()).toContain('小日子雜貨舖')
    expect(wrapper.text()).toContain('3C 配件')
    expect(wrapper.findAll('.card')).toHaveLength(4)
  })

  it('商品列表可以依網址條件搜尋並換頁', async () => {
    const { wrapper, router } = await mountWithApp(ProductListView, '/products')
    expect(wrapper.text()).toContain('共 16 件商品')
    await router.push('/products?q=杯')
    await settle()
    expect(wrapper.text()).toContain('共 3 件商品')
    await router.push('/products?q=不存在的東西')
    await settle()
    expect(wrapper.text()).toContain('找不到符合條件的商品')
    await router.push('/products?min_price=900&max_price=100')
    await settle()
    expect(wrapper.text()).toContain('最低價格不能高於最高價格')
  })

  it('套用篩選會更新網址；分頁換到第 2 頁', async () => {
    const { wrapper, router } = await mountWithApp(ProductListView, '/products')
    await wrapper.find('#f-cat').setValue(2)
    await wrapper.find('#f-min').setValue(100)
    await wrapper.find('#f-sort').setValue('price_desc')
    await wrapper.find('.filters').trigger('submit')
    await settle()
    expect(router.currentRoute.value.query).toMatchObject({
      category_id: '2',
      min_price: '100',
      sort: 'price_desc',
    })
    await router.push('/products')
    await settle()
    await wrapper.findAll('.pager button')[1]!.trigger('click')
    await settle()
    expect(router.currentRoute.value.query.page).toBe('2')
  })

  it('商品詳情：未登入加入購物車會帶去登入頁', async () => {
    const { wrapper, router } = await mountWithApp(ProductDetailView, '/products/1')
    expect(wrapper.text()).toContain('手沖咖啡濾杯')
    expect(wrapper.text()).toContain('NT$680')
    await wrapper.find('.buy .btn').trigger('click')
    await settle()
    expect(router.currentRoute.value.name).toBe('login')
    expect(router.currentRoute.value.query.redirect).toBe('/products/1')
  })

  it('商品詳情：登入後加入購物車；不存在的商品顯示找不到', async () => {
    loginAs(2)
    const { wrapper } = await mountWithApp(ProductDetailView, '/products/1')
    await wrapper.find('.buy .btn').trigger('click')
    await settle()
    expect(wrapper.text()).toContain('已加入購物車')
    const missing = await mountWithApp(ProductDetailView, '/products/999')
    expect(missing.wrapper.text()).toContain('找不到這個商品')
  })

  it('售完商品不顯示購買按鈕', async () => {
    const { wrapper } = await mountWithApp(ProductDetailView, '/products/16')
    expect(wrapper.text()).toContain('已售完')
    expect(wrapper.find('.buy').exists()).toBe(false)
  })
})

describe('購物流程', () => {
  it('購物車：改數量、超過庫存顯示錯誤、移除', async () => {
    loginAs(2)
    db.carts[2] = { 1: 1, 12: 1 }
    const { wrapper } = await mountWithApp(CartView, '/cart')
    expect(wrapper.text()).toContain('NT$2,180')
    await wrapper.findAll('button[aria-label="增加一件"]')[0]!.trigger('click')
    await settle()
    expect(wrapper.text()).toContain('NT$2,860')
    db.products.find((p) => p.id === 12)!.stock = 0
    await wrapper.findAll('.line .btn--ghost')[1]!.trigger('click')
    await settle()
    expect(wrapper.findAll('.line')).toHaveLength(1)
  })

  it('購物車是空的時候提示去逛逛', async () => {
    loginAs(2)
    const { wrapper } = await mountWithApp(CartView, '/cart')
    expect(wrapper.text()).toContain('購物車是空的')
  })

  it('結帳：新增地址、套用優惠碼、送出訂單後前往訂單頁', async () => {
    loginAs(2)
    db.carts[2] = { 4: 1, 13: 1 } // 450 + 290 = 740
    const { wrapper, router } = await mountWithApp(CheckoutView, '/checkout')
    expect(wrapper.text()).toContain('NT$800') // 740 + 運費 60

    await wrapper.find('#a-name').setValue('王小明')
    await wrapper.find('#a-phone').setValue('0912345678')
    await wrapper.find('#a-zip').setValue('100')
    await wrapper.find('#a-city').setValue('台北市')
    await wrapper.find('#a-line').setValue('重慶南路一段 1 號')
    await wrapper.find('.new').trigger('submit')
    await settle()
    expect(wrapper.text()).toContain('王小明')

    await wrapper.find('#coupon').setValue('EXPIRED50')
    await wrapper.find('.coupon').trigger('submit')
    await settle()
    expect(wrapper.text()).toContain('已過期')

    await wrapper.find('#coupon').setValue('welcome100')
    await wrapper.find('.coupon').trigger('submit')
    await settle()
    expect(wrapper.text()).toContain('NT$700')

    await wrapper.find('.submit').trigger('click')
    await settle()
    expect(router.currentRoute.value.name).toBe('order')
    expect(db.orders[0]?.total).toBe(700)
    expect(db.products.find((p) => p.id === 4)!.stock).toBe(29)
  })

  it('結帳：取消優惠碼、地址格式錯誤提示、購物車空時顯示錯誤', async () => {
    loginAs(2)
    db.carts[2] = { 2: 1, 6: 1 }
    db.addresses[2] = [
      { id: 1, recipient: '王', phone: '0912345678', postal_code: '100', city: '台北市', line: '路' },
    ]
    const { wrapper } = await mountWithApp(CheckoutView, '/checkout')
    expect(wrapper.text()).toContain('免運')
    await wrapper.find('#coupon').setValue('SAVE10')
    await wrapper.find('.coupon').trigger('submit')
    await settle()
    expect(wrapper.text()).toContain('SAVE10')
    await wrapper.findAll('.coupon button')[1]!.trigger('click')
    await settle()
    expect(wrapper.text()).not.toContain('（SAVE10）')

    await wrapper.find('.picker > .btn').trigger('click')
    await wrapper.find('#a-phone').setValue('123')
    await wrapper.find('.new').trigger('submit')
    await settle()
    expect(wrapper.text()).toContain('請檢查電話')

    db.carts[2] = {}
    const empty = await mountWithApp(CheckoutView, '/checkout')
    expect(empty.wrapper.text()).toContain('購物車是空的')
  })

  it('訂單：列表、付款、取消', async () => {
    loginAs(2)
    db.carts[2] = { 1: 1 }
    db.addresses[2] = [
      { id: 1, recipient: '王', phone: '0912345678', postal_code: '100', city: '台北市', line: '路' },
    ]
    const list0 = await mountWithApp(OrderListView, '/orders')
    expect(list0.wrapper.text()).toContain('還沒有訂單')

    const checkout = await mountWithApp(CheckoutView, '/checkout')
    await checkout.wrapper.find('.submit').trigger('click')
    await settle()
    const id = db.orders[0]!.id

    const detail = await mountWithApp(OrderDetailView, `/orders/${id}?created=1`)
    expect(detail.wrapper.text()).toContain('訂單已成立')
    await detail.wrapper.find('.actions .btn').trigger('click')
    await settle()
    expect(detail.wrapper.text()).toContain('付款完成')
    expect(detail.wrapper.text()).toContain('已付款')

    db.carts[2] = { 5: 1 }
    const c2 = await mountWithApp(CheckoutView, '/checkout')
    await c2.wrapper.find('.submit').trigger('click')
    await settle()
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    const d2 = await mountWithApp(OrderDetailView, `/orders/${db.orders[1]!.id}`)
    await d2.wrapper.find('.actions .btn--ghost').trigger('click')
    await settle()
    expect(d2.wrapper.text()).toContain('訂單已取消')

    const list = await mountWithApp(OrderListView, '/orders')
    expect(list.wrapper.findAll('tbody tr')).toHaveLength(2)
    const missing = await mountWithApp(OrderDetailView, '/orders/9999')
    expect(missing.wrapper.text()).toContain('找不到這筆訂單')
  })
})

describe('會員', () => {
  it('登入成功後回到 redirect；外部網址一律回首頁', async () => {
    const { wrapper, router } = await mountWithApp(LoginView, '/login?redirect=/cart')
    await wrapper.find('#email').setValue('demo@example.com')
    await wrapper.find('#password').setValue('demo12345')
    await wrapper.find('form').trigger('submit')
    await settle()
    expect(router.currentRoute.value.path).toBe('/cart')

    db.currentUserId = null
    const evil = await mountWithApp(LoginView, '/login?redirect=//evil.example')
    await evil.wrapper.find('#email').setValue('demo@example.com')
    await evil.wrapper.find('#password').setValue('demo12345')
    await evil.wrapper.find('form').trigger('submit')
    await settle()
    expect(evil.router.currentRoute.value.path).toBe('/')
  })

  it('登入失敗顯示錯誤', async () => {
    const { wrapper } = await mountWithApp(LoginView, '/login')
    await wrapper.find('#email').setValue('demo@example.com')
    await wrapper.find('#password').setValue('nope')
    await wrapper.find('form').trigger('submit')
    await settle()
    expect(wrapper.find('[role="alert"]').text()).toBe('Email 或密碼錯誤')
  })

  it('註冊：重複 Email 顯示錯誤；成功後登入', async () => {
    const { wrapper, router } = await mountWithApp(RegisterView, '/register')
    await wrapper.find('#name').setValue('小美')
    await wrapper.find('#email').setValue('demo@example.com')
    await wrapper.find('#password').setValue('password123')
    await wrapper.find('form').trigger('submit')
    await settle()
    expect(wrapper.text()).toContain('已經註冊過了')
    await wrapper.find('#email').setValue('may@example.com')
    await wrapper.find('form').trigger('submit')
    await settle()
    expect(router.currentRoute.value.path).toBe('/')
  })

  it('路由守衛：未登入不能進購物車；一般會員不能進後台', async () => {
    const guest = await mountWithApp(NotFoundView, '/cart')
    expect(guest.router.currentRoute.value.name).toBe('login')
    loginAs(2)
    const member = await mountWithApp(NotFoundView, '/admin/orders')
    expect(member.router.currentRoute.value.name).toBe('home')
  })
})

describe('版面與後台', () => {
  it('App：頁首顯示購物車數量、管理員看得到後台、可以搜尋與登出', async () => {
    loginAs(1)
    db.carts[1] = { 1: 2 }
    const { wrapper, router } = await mountWithApp(App, '/faq')
    expect(wrapper.find('[data-test="cart-link"]').text()).toContain('2')
    expect(wrapper.text()).toContain('後台')
    expect(wrapper.text()).toContain('運費怎麼算')
    await wrapper.find('#site-search').setValue('筆')
    await wrapper.find('form[role="search"]').trigger('submit')
    await settle()
    expect(router.currentRoute.value.fullPath).toBe('/products?q=%E7%AD%86')
    await wrapper.find('.link-btn').trigger('click')
    await settle()
    expect(wrapper.text()).toContain('登入')
  })

  it('FAQ 與 404 頁', async () => {
    expect((await mountWithApp(FaqView, '/faq')).wrapper.findAll('dt').length).toBeGreaterThan(3)
    expect((await mountWithApp(NotFoundView, '/nope')).wrapper.text()).toContain('找不到這個頁面')
  })

  it('後台商品：改價格存檔、新增商品', async () => {
    loginAs(1)
    const { wrapper } = await mountWithApp(AdminProductsView, '/admin/products')
    expect(wrapper.findAll('tbody tr')).toHaveLength(16)
    await wrapper.find('input[aria-label="手沖咖啡濾杯 價格"]').setValue(700)
    await wrapper.find('tbody tr .btn').trigger('click')
    await settle()
    expect(db.products[0]!.price).toBe(700)
    expect(wrapper.text()).toContain('已儲存')

    await wrapper.find('input[aria-label="手沖咖啡濾杯 價格"]').setValue(-1)
    await wrapper.find('tbody tr .btn').trigger('click')
    await settle()
    expect(wrapper.text()).toContain('#1：')

    await wrapper.find('#n-name').setValue('新的杯子')
    await wrapper.find('#n-price').setValue(300)
    await wrapper.find('#n-stock').setValue(5)
    await wrapper.find('.add').trigger('submit')
    await settle()
    expect(wrapper.findAll('tbody tr')).toHaveLength(17)
  })

  it('後台訂單：出貨、篩選', async () => {
    loginAs(1)
    db.orders.push({
      id: 500,
      user_id: 2,
      idempotency_key: 'k',
      status: 'paid',
      subtotal: 680,
      discount: 0,
      shipping_fee: 60,
      total: 740,
      currency: 'TWD',
      coupon_code: null,
      recipient_name: '王',
      recipient_phone: '0912345678',
      shipping_address: '100 台北市',
      created_at: '2026-11-25T00:00:00Z',
      items: [{ product_id: 1, product_name: '手沖咖啡濾杯', unit_price: 680, quantity: 1, line_total: 680 }],
    })
    const { wrapper } = await mountWithApp(AdminOrdersView, '/admin/orders')
    expect(wrapper.text()).toContain('出貨')
    await wrapper.find('tbody .btn').trigger('click')
    await settle()
    expect(db.orders[0]!.status).toBe('shipped')
    await wrapper.find('#st').setValue('cancelled')
    await settle()
    expect(wrapper.text()).toContain('目前沒有符合的訂單')
  })
})
