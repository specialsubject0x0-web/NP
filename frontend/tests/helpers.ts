// 測試小工具：建立帶路由與 Pinia 的元件、等待非同步完成。
import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import type { Component } from 'vue'
import { createMemoryHistory } from 'vue-router'
import { createAppRouter } from '@/router'

export async function mountWithApp(component: Component, path = '/', props: Record<string, unknown> = {}) {
  const pinia = createPinia()
  setActivePinia(pinia)
  const router = createAppRouter(createMemoryHistory())
  await router.push(path)
  await router.isReady()
  const wrapper = mount(component, { props, global: { plugins: [pinia, router] } })
  await settle()
  return { wrapper, router, pinia }
}

/** 等所有 API 回應與畫面更新完成。 */
export async function settle(): Promise<void> {
  for (let i = 0; i < 5; i++) {
    await flushPromises()
    await new Promise((r) => setTimeout(r, 0))
  }
}
