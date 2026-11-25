// ESLint 設定：檢查 Vue 與 TypeScript 的常見錯誤。
import pluginVue from 'eslint-plugin-vue'
import { defineConfigWithVueTs, vueTsConfigs } from '@vue/eslint-config-typescript'

export default defineConfigWithVueTs(
  { ignores: ['dist/**', 'coverage/**', 'public/**', 'src/types/**', 'playwright-report/**', 'test-results/**'] },
  pluginVue.configs['flat/recommended'],
  vueTsConfigs.recommended,
  {
    rules: {
      // 【重要】禁止 v-html（AGENTS.md 5.2，避免 XSS）
      'vue/no-v-html': 'error',
      // 格式交給 Prettier
      'vue/max-attributes-per-line': 'off',
      'vue/html-closing-bracket-newline': 'off',
      'vue/html-indent': 'off',
      'vue/multiline-html-element-content-newline': 'off',
      'vue/singleline-html-element-content-newline': 'off',
      'vue/html-self-closing': 'off',
      'vue/multi-word-component-names': 'off',
      // 以底線開頭的變數代表「故意不用」（例如從物件中拿掉某個欄位）
      '@typescript-eslint/no-unused-vars': ['error', { varsIgnorePattern: '^_', argsIgnorePattern: '^_' }],
      // 【重要】元件內不得直接呼叫 fetch，一律透過 src/api/（AGENTS.md 3.9 B5）
      'no-restricted-globals': ['error', { name: 'fetch', message: '請改用 src/api/ 的函式' }],
    },
  },
  {
    files: ['src/api/client.ts', 'tests/**', 'e2e/**'],
    rules: { 'no-restricted-globals': 'off' },
  },
)
