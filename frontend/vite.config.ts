// Vite 設定：開發伺服器、建置、Vitest 測試。
// 一般開發（npm run dev）會把 /api 轉給本機後端 http://127.0.0.1:8000，
// 這樣前端和 API 看起來是同一個網址，Cookie 才能正常運作。
// 【可修改】後端不是跑在 8000 port 時，改 .env 的 VITE_API_PROXY_TARGET。
import { fileURLToPath, URL } from 'node:url'
import vue from '@vitejs/plugin-vue'
import { defineConfig, loadEnv } from 'vite'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), 'VITE_')
  return {
    plugins: [vue()],
    resolve: { alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) } },
    server: {
      port: 5173,
      proxy: { '/api': { target: env.VITE_API_PROXY_TARGET || 'http://127.0.0.1:8000', changeOrigin: false } },
    },
    test: {
      environment: 'jsdom',
      include: ['tests/**/*.spec.ts'],
      setupFiles: ['tests/setup.ts'],
      coverage: {
        provider: 'v8',
        include: ['src/**/*.{ts,vue}'],
        exclude: ['src/types/**', 'src/main.ts', 'src/mocks/**', 'src/**/*.d.ts'],
        thresholds: { lines: 70, statements: 70, functions: 70, branches: 70 },
      },
    },
  }
})
