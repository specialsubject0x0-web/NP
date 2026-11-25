// Playwright E2E 設定：自動啟動 Mock 模式（不需後端），用真的瀏覽器跑一遍主流程。
// 執行：npm run e2e（第一次要先 npx playwright install chromium）
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: 'e2e',
  timeout: 30_000,
  use: { baseURL: 'http://localhost:4173', trace: 'retain-on-failure' },
  // 【可修改】已安裝 Google Chrome 時可用 PW_CHANNEL=chrome npm run e2e，不必另外下載瀏覽器
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'], channel: process.env.PW_CHANNEL } }],
  webServer: {
    command: 'npm run dev:mock -- --port 4173 --strictPort',
    url: 'http://localhost:4173',
    reuseExistingServer: !process.env.CI,
  },
})
