// 登入狀態（Pinia store）：記住「目前是誰登入」，讓頁首、路由守衛都能用。
// 【為什麼】登入憑證放在 httpOnly Cookie，JavaScript 讀不到；這裡只存使用者的公開資料（名字、角色）。
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import * as authApi from '@/api/auth'
import type { User } from '@/api/types'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const checked = ref(false) // 是否已經問過後端「我是誰」

  const isLoggedIn = computed(() => user.value !== null)
  const isAdmin = computed(() => user.value?.role === 'admin')

  /** 網站開啟時問一次後端：目前有沒有登入？ */
  async function load(): Promise<void> {
    if (checked.value) return
    try {
      user.value = await authApi.fetchMe()
    } catch {
      user.value = null
    } finally {
      checked.value = true
    }
  }

  async function login(email: string, password: string): Promise<void> {
    user.value = await authApi.login(email, password)
    checked.value = true
  }

  async function register(email: string, password: string, name: string): Promise<void> {
    user.value = await authApi.register(email, password, name)
    checked.value = true
  }

  async function logout(): Promise<void> {
    await authApi.logout()
    user.value = null
  }

  return { user, checked, isLoggedIn, isAdmin, load, login, register, logout }
})
