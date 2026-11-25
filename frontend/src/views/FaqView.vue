<!-- 常見問題：內容在 content/faq.json（【手動修改區】）。 -->
<script setup lang="ts">
import faq from '@/content/faq.json'
</script>

<template>
  <div class="page">
    <h1>{{ faq.title }}</h1>
    <dl class="faq">
      <template v-for="item in faq.items" :key="item.q">
        <dt>{{ item.q }}</dt>
        <dd>{{ item.a }}</dd>
      </template>
    </dl>
  </div>
</template>

<style scoped>
.faq {
  max-width: 44em;
}
dt {
  font-family: var(--font-display);
  font-size: var(--text-lg);
  font-weight: 700;
  margin-top: var(--space-5);
}
dd {
  margin: var(--space-2) 0 0;
}
</style>
