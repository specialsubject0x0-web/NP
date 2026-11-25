<!-- 註冊（US-008）。密碼至少 8 個字（R-16），註冊成功直接登入。 -->
<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ErrorMessage from '@/components/ErrorMessage.vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const name = ref('')
const email = ref('')
const password = ref('')
const error = ref<string | null>(null)

async function submit(): Promise<void> {
  error.value = null
  try {
    await auth.register(email.value, password.value, name.value)
    const r = route.query.redirect
    void router.push(typeof r === 'string' && r.startsWith('/') && !r.startsWith('//') ? r : '/')
  } catch (e) {
    error.value = (e as Error).message
  }
}
</script>

<template>
  <div class="page narrow">
    <h1>註冊</h1>
    <form class="panel" @submit.prevent="submit">
      <div class="field">
        <label for="name">名字</label
        ><input id="name" v-model="name" required maxlength="50" autocomplete="name" />
      </div>
      <div class="field">
        <label for="email">Email</label
        ><input id="email" v-model="email" type="email" required autocomplete="email" />
      </div>
      <div class="field">
        <label for="password">密碼（至少 8 個字）</label>
        <input
          id="password"
          v-model="password"
          type="password"
          required
          minlength="8"
          autocomplete="new-password"
        />
      </div>
      <ErrorMessage :message="error" />
      <button type="submit" class="btn">註冊並登入</button>
    </form>
  </div>
</template>

<style scoped>
.narrow {
  max-width: 440px;
}
</style>
