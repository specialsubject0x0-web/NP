<!-- 最外層版面：頁首 + 目前頁面 + 頁尾。 -->
<script setup lang="ts">
import SiteFooter from '@/components/SiteFooter.vue'
import SiteHeader from '@/components/SiteHeader.vue'
</script>

<template>
  <a class="skip" href="#main">跳到主要內容</a>
  <SiteHeader />
  <main id="main">
    <RouterView />
  </main>
  <SiteFooter />
</template>

<style scoped>
.skip {
  position: absolute;
  left: -999px;
}
.skip:focus {
  left: var(--space-3);
  top: var(--space-3);
  z-index: 10;
  background: #fff;
  padding: var(--space-2) var(--space-3);
}
main {
  min-height: 60vh;
}
</style>
