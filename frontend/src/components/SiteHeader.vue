<!--
  頁首：店名、搜尋框、導覽連結、購物車數量、登入狀態。
  店名與標語來自 config/site.config.ts；顏色來自 theme/tokens.css 的 --color-ink。
-->
<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { siteConfig } from '@/config/site.config'
import { useAuthStore } from '@/stores/auth'
import { useCartStore } from '@/stores/cart'

const auth = useAuthStore()
const cartStore = useCartStore()
const router = useRouter()
const keyword = ref('')

// 登入後自動讀取購物車，讓「購物車 (N)」顯示正確數量
watch(
  () => auth.isLoggedIn,
  (loggedIn) => {
    if (loggedIn) void cartStore.refresh().catch(() => undefined)
    else cartStore.clear()
  },
  { immediate: true },
)

function search(): void {
  void router.push({ name: 'products', query: keyword.value ? { q: keyword.value } : {} })
}

async function logout(): Promise<void> {
  await auth.logout()
  void router.push({ name: 'home' })
}
</script>

<template>
  <header class="header">
    <div class="inner">
      <RouterLink to="/" class="brand">
        <span class="brand-name">{{ siteConfig.shopName }}</span>
        <span class="brand-tagline">{{ siteConfig.tagline }}</span>
      </RouterLink>

      <form class="search" role="search" @submit.prevent="search">
        <label for="site-search" class="visually-hidden">搜尋商品</label>
        <input id="site-search" v-model="keyword" type="search" placeholder="搜尋商品" maxlength="50" />
        <button type="submit" class="search-btn">搜尋</button>
      </form>

      <nav class="nav" aria-label="主要導覽">
        <RouterLink to="/products">全部商品</RouterLink>
        <RouterLink v-if="siteConfig.showFaqLink" to="/faq">常見問題</RouterLink>
        <RouterLink to="/cart" data-test="cart-link">
          購物車<span v-if="cartStore.cart?.item_count" class="count">{{ cartStore.cart.item_count }}</span>
        </RouterLink>
        <template v-if="auth.isLoggedIn">
          <RouterLink to="/orders">我的訂單</RouterLink>
          <RouterLink v-if="auth.isAdmin" to="/admin/products">後台</RouterLink>
          <button type="button" class="link-btn" @click="logout">登出 {{ auth.user?.name }}</button>
        </template>
        <RouterLink v-else to="/login">登入</RouterLink>
      </nav>
    </div>
  </header>
</template>

<style scoped>
.header {
  background: var(--color-ink);
  color: #fff;
}
.inner {
  max-width: var(--page-width);
  margin: 0 auto;
  padding: var(--space-3) var(--space-4);
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-3) var(--space-5);
}
.brand {
  color: #fff;
  text-decoration: none;
  display: flex;
  align-items: baseline;
  gap: var(--space-3);
}
.brand-name {
  font-family: var(--font-display);
  font-size: var(--text-lg);
  font-weight: 700;
  letter-spacing: 0.08em;
}
.brand-tagline {
  font-size: var(--text-sm);
  opacity: 0.75;
}
.search {
  display: flex;
  flex: 1 1 200px;
  max-width: 320px;
}
.search input {
  flex: 1;
  min-width: 0;
  height: 36px;
  border: 0;
  border-radius: var(--radius) 0 0 var(--radius);
  padding: 0 var(--space-3);
  font: inherit;
}
.search-btn {
  height: 36px;
  border: 0;
  border-radius: 0 var(--radius) var(--radius) 0;
  padding: 0 var(--space-3);
  background: #fff;
  color: var(--color-ink);
  font: inherit;
  font-weight: 600;
  cursor: pointer;
  border-left: 1px solid var(--color-line);
}
.nav {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-4);
  margin-left: auto;
  align-items: center;
}
.nav a,
.link-btn {
  color: #fff;
  text-decoration: none;
  font-size: var(--text-sm);
}
.nav a.router-link-active {
  text-decoration: underline;
  text-underline-offset: 6px;
}
.link-btn {
  background: none;
  border: 0;
  cursor: pointer;
  font: inherit;
  font-size: var(--text-sm);
  padding: 0;
}
.count {
  display: inline-block;
  min-width: 1.4em;
  margin-left: var(--space-1);
  padding: 0 var(--space-1);
  border-radius: 999px;
  background: var(--color-seal);
  text-align: center;
  font-size: 0.75rem;
  line-height: 1.4em;
}
</style>
