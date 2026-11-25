<!-- 登入（US-008）。成功後回到原本想去的頁面（網址上的 redirect）。 -->
<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ErrorMessage from '@/components/ErrorMessage.vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const email = ref('')
const password = ref('')
const error = ref<string | null>(null)
const busy = ref(false)

// 【重要】只允許站內路徑（以 / 開頭、不是 //），避免被導到外部釣魚網站（開放重新導向漏洞）
function safeRedirect(value: unknown): string {
  return typeof value === 'string' && value.startsWith('/') && !value.startsWith('//') ? value : '/'
}

async function submit(): Promise<void> {
  busy.value = true
  error.value = null
  try {
    await auth.login(email.value, password.value)
    void router.push(safeRedirect(route.query.redirect))
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div class="page narrow">
    <h1>登入</h1>
    <form class="panel" @submit.prevent="submit">
      <div class="field">
        <label for="email">Email</label
        ><input id="email" v-model="email" type="email" required autocomplete="email" />
      </div>
      <div class="field">
        <label for="password">密碼</label>
        <input id="password" v-model="password" type="password" required autocomplete="current-password" />
      </div>
      <ErrorMessage :message="error" />
      <button type="submit" class="btn" :disabled="busy">登入</button>
      <p class="muted">
        還沒有帳號？<RouterLink :to="{ name: 'register', query: route.query }">註冊</RouterLink>
      </p>
      <p class="muted small">示範帳號：demo@example.com／demo12345</p>
    </form>
  </div>
</template>

<style scoped>
.narrow {
  max-width: 440px;
}
.small {
  font-size: var(--text-sm);
}
</style>
