// 前端程式進入點：建立 Vue 應用程式，掛上路由與狀態管理。
// Mock 模式（npm run dev:mock）會先啟動 MSW 假後端，不需要真的後端就能操作整個網站。
import { createPinia } from 'pinia'
import { createApp } from 'vue'
import App from './App.vue'
import { siteConfig } from './config/site.config'
import { createAppRouter } from './router'
import './theme/tokens.css'
import './theme/base.css'

async function start(): Promise<void> {
  if (import.meta.env.MODE === 'mock') {
    const { startMockWorker } = await import('./mocks/browser')
    await startMockWorker()
  }
  document.title = siteConfig.shopName
  createApp(App).use(createPinia()).use(createAppRouter()).mount('#app')
}

void start()
