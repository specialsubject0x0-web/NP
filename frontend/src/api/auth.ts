// 會員相關 API（登入、註冊、登出、目前登入者）。
import { request } from './client'
import type { User } from './types'

export const fetchMe = () => request<User>('GET', '/auth/me')
export const login = (email: string, password: string) =>
  request<User>('POST', '/auth/login', { body: { email, password } })
export const register = (email: string, password: string, name: string) =>
  request<User>('POST', '/auth/register', { body: { email, password, name } })
export const logout = () => request<void>('POST', '/auth/logout')
