// 購物車與收件地址 API（需登入）。
import { request } from './client'
import type { Address, AddressInput, Cart } from './types'

export const fetchCart = () => request<Cart>('GET', '/cart')
/** 設定某商品在購物車的數量（不是加上去，是「改成」這個數量）。 */
export const setCartItem = (productId: number, quantity: number) =>
  request<Cart>('PUT', `/cart/items/${productId}`, { body: { quantity } })
export const removeCartItem = (productId: number) => request<Cart>('DELETE', `/cart/items/${productId}`)

export const fetchAddresses = () => request<Address[]>('GET', '/addresses')
export const createAddress = (data: AddressInput) => request<Address>('POST', '/addresses', { body: data })
export const deleteAddress = (id: number) => request<void>('DELETE', `/addresses/${id}`)
