<!--
  庫存印章：庫存少時蓋上紅色「僅剩 N 件」，賣完顯示「已售完」，庫存充足時不顯示。
  【可修改】「少」的標準在 config/site.config.ts 的 lowStockThreshold。
-->
<script setup lang="ts">
import { siteConfig } from '@/config/site.config'

defineProps<{ stock: number }>()
</script>

<template>
  <span v-if="stock === 0" class="stamp stamp--out">已售完</span>
  <span v-else-if="stock <= siteConfig.lowStockThreshold" class="stamp">僅剩 {{ stock }} 件</span>
</template>

<style scoped>
.stamp {
  display: inline-block;
  padding: 2px var(--space-2);
  border: 2px solid var(--color-seal);
  border-radius: 3px;
  color: var(--color-seal);
  font-family: var(--font-display);
  font-weight: 700;
  font-size: var(--text-sm);
  transform: rotate(-4deg);
  background: rgb(255 255 255 / 0.9);
}
.stamp--out {
  border-color: var(--color-muted);
  color: var(--color-muted);
}
</style>
