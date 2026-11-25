// Vitest 共用設定：用 MSW 的假後端（和 dev:mock 同一份 handlers）回應 API，每個測試前把假資料還原。
import { setupServer } from 'msw/node'
import { afterAll, afterEach, beforeAll, beforeEach } from 'vitest'
import { resetCsrfForTests } from '@/api/client'
import { handlers } from '@/mocks/handlers'
import { resetDb } from '@/mocks/db'

// jsdom 沒有實作捲動，路由換頁時會呼叫它，這裡用空函式代替
window.scrollTo = () => undefined

export const server = setupServer(...handlers)

beforeAll(() => server.listen())
beforeEach(() => {
  resetDb()
  resetCsrfForTests()
})
afterEach(() => server.resetHandlers())
afterAll(() => server.close())
