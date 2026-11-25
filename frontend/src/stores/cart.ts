// 購物車狀態：讓頁首的「購物車 (3)」和購物車頁共用同一份資料。
import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as cartApi from '@/api/cart'
import type { Cart } from '@/api/types'

export const useCartStore = defineStore('cart', () => {
  const cart = ref<Cart | null>(null)

  async function refresh(): Promise<void> {
    cart.value = await cartApi.fetchCart()
  }

  async function setQuantity(productId: number, quantity: number): Promise<void> {
    cart.value = await cartApi.setCartItem(productId, quantity)
  }

  /** 加入購物車：已經有的商品就把數量加上去（上限交給後端檢查）。 */
  async function add(productId: number, quantity = 1): Promise<void> {
    const current = cart.value?.items.find((i) => i.product_id === productId)?.quantity ?? 0
    await setQuantity(productId, current + quantity)
  }

  async function remove(productId: number): Promise<void> {
    cart.value = await cartApi.removeCartItem(productId)
  }

  function clear(): void {
    cart.value = null
  }

  return { cart, refresh, setQuantity, add, remove, clear }
})
