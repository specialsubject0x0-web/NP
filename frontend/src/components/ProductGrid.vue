<!--
  商品格線：每列幾個由 config/site.config.ts 的 productsPerRow 決定（【可修改】）。
  螢幕變窄時自動減少每列數量。
-->
<script setup lang="ts">
import type { Product } from '@/api/types'
import { siteConfig } from '@/config/site.config'
import ProductCard from './ProductCard.vue'

defineProps<{ products: Product[] }>()
</script>

<template>
  <div class="grid" :style="{ '--per-row': siteConfig.productsPerRow }">
    <ProductCard v-for="p in products" :key="p.id" :product="p" />
  </div>
</template>

<style scoped>
.grid {
  display: grid;
  gap: var(--space-4);
  grid-template-columns: repeat(var(--per-row), minmax(0, 1fr));
}
@media (max-width: 900px) {
  .grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}
@media (max-width: 640px) {
  .grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
