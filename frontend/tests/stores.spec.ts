// Pinia stores：登入狀態與購物車。
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it } from 'vitest'
import { db } from '@/mocks/db'
import { useAuthStore } from '@/stores/auth'
import { useCartStore } from '@/stores/cart'

beforeEach(() => setActivePinia(createPinia()))

describe('auth store', () => {
  it('未登入時 load 後為訪客', async () => {
    const auth = useAuthStore()
    await auth.load()
    expect(auth.isLoggedIn).toBe(false)
    expect(auth.checked).toBe(true)
  })

  it('登入、判斷管理員、登出', async () => {
    const auth = useAuthStore()
    await auth.login('admin@example.com', 'admin12345')
    expect(auth.isAdmin).toBe(true)
    await auth.logout()
    expect(auth.user).toBeNull()
  })

  it('登入失敗會丟出錯誤訊息', async () => {
    await expect(useAuthStore().login('demo@example.com', 'wrong')).rejects.toThrow('Email 或密碼錯誤')
  })

  it('註冊後直接登入', async () => {
    const auth = useAuthStore()
    await auth.register('new@example.com', 'password123', '新朋友')
    expect(auth.user?.name).toBe('新朋友')
  })
})

describe('cart store', () => {
  it('加入同一商品會累加數量、可移除', async () => {
    db.currentUserId = 2
    const cart = useCartStore()
    await cart.refresh()
    await cart.add(1)
    await cart.add(1, 2)
    expect(cart.cart?.items[0]?.quantity).toBe(3)
    await cart.remove(1)
    expect(cart.cart?.item_count).toBe(0)
    cart.clear()
    expect(cart.cart).toBeNull()
  })

  it('超過庫存時丟出後端訊息', async () => {
    db.currentUserId = 2
    await expect(useCartStore().add(12, 2)).rejects.toThrow('庫存只剩 1 件')
  })
})
