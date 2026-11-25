// 小元件：商品圖、庫存印章、數量、金額明細、分頁、狀態標籤、篩選。
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import OrderStatusBadge from '@/components/OrderStatusBadge.vue'
import PaginationNav from '@/components/PaginationNav.vue'
import PriceSummary from '@/components/PriceSummary.vue'
import ProductFilters from '@/components/ProductFilters.vue'
import ProductImage from '@/components/ProductImage.vue'
import QuantityInput from '@/components/QuantityInput.vue'
import StockStamp from '@/components/StockStamp.vue'
import { formatDate, formatPrice } from '@/composables/format'

describe('format', () => {
  it('金額加上千分位與 NT$', () => expect(formatPrice(12345)).toBe('NT$12,345'))
  it('UTC 時間轉成台灣時間', () => expect(formatDate('2026-11-25T16:30:00Z')).toMatch(/2026\/11\/26\s00:30/))
})

describe('ProductImage', () => {
  it('取商品名第一個中文字，並提供替代文字', () => {
    const w = mount(ProductImage, { props: { name: '0.5 鋼珠筆（五色組）', color: '#123456' } })
    expect(w.text()).toBe('鋼')
    expect(w.attributes('role')).toBe('img')
    expect(w.attributes('aria-label')).toBe('0.5 鋼珠筆（五色組）')
  })
})

describe('StockStamp', () => {
  it.each([
    [0, '已售完'],
    [2, '僅剩 2 件'],
    [50, ''],
  ])('庫存 %i 顯示「%s」', (stock, text) => {
    expect(mount(StockStamp, { props: { stock } }).text()).toBe(text)
  })
})

describe('QuantityInput', () => {
  it('不會小於 1、不會超過庫存', async () => {
    const w = mount(QuantityInput, { props: { modelValue: 1, max: 2 } })
    expect(w.find('button[aria-label="減少一件"]').attributes('disabled')).toBeDefined()
    await w.find('button[aria-label="增加一件"]').trigger('click')
    expect(w.emitted('update:modelValue')?.[0]).toEqual([2])
    await w.find('input').setValue('999')
    expect(w.emitted('update:modelValue')?.at(-1)).toEqual([2])
    await w.find('input').setValue('abc')
    expect(w.emitted('update:modelValue')?.at(-1)).toEqual([1])
  })
})

describe('PriceSummary', () => {
  it('免運與折扣顯示', () => {
    const w = mount(PriceSummary, {
      props: { subtotal: 1200, discount: 100, shippingFee: 0, total: 1100, couponCode: 'WELCOME100' },
    })
    expect(w.text()).toContain('免運')
    expect(w.text()).toContain('WELCOME100')
    expect(w.text()).toContain('NT$1,100')
  })
})

describe('PaginationNav', () => {
  it('只有一頁時不顯示；多頁時可以換頁', async () => {
    expect(mount(PaginationNav, { props: { page: 1, pageSize: 10, total: 5 } }).html()).toBe('<!--v-if-->')
    const w = mount(PaginationNav, { props: { page: 1, pageSize: 10, total: 25 } })
    expect(w.text()).toContain('第 1 / 3 頁')
    await w.findAll('button')[1]!.trigger('click')
    expect(w.emitted('change')?.[0]).toEqual([2])
  })
})

describe('OrderStatusBadge', () => {
  it('顯示中文狀態', () => {
    expect(mount(OrderStatusBadge, { props: { status: 'pending_payment' } }).text()).toBe('待付款')
  })
})

describe('ProductFilters', () => {
  it('送出目前的篩選條件', async () => {
    const w = mount(ProductFilters, {
      props: {
        categories: [{ id: 1, name: '廚房', slug: 'kitchen' }],
        modelValue: { q: '', category_id: null, min_price: null, max_price: null, sort: 'newest' },
      },
    })
    await w.find('#f-q').setValue('杯')
    await w.find('#f-sort').setValue('price_asc')
    await w.find('form').trigger('submit')
    expect(w.emitted('apply')?.[0]?.[0]).toMatchObject({ q: '杯', sort: 'price_asc' })
    await w.setProps({
      modelValue: { q: '筆', category_id: 1, min_price: null, max_price: null, sort: 'name' },
    })
    expect((w.find('#f-q').element as HTMLInputElement).value).toBe('筆')
  })
})
