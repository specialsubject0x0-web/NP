// 在瀏覽器啟動 MSW（只有 npm run dev:mock 會用到）。
import { setupWorker } from 'msw/browser'
import { handlers } from './handlers'

export async function startMockWorker(): Promise<void> {
  await setupWorker(...handlers).start({ quiet: true })
  console.info('[Mock 模式] 目前使用假後端，資料重新整理後會還原。示範帳號：demo@example.com／demo12345')
}
