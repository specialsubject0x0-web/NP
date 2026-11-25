<!-- 商品卡片：圖、名稱、價格、庫存印章。點整張卡片進入商品詳情。 -->
<script setup lang="ts">
import type { Product } from '@/api/types'
import { formatPrice } from '@/composables/format'
import ProductImage from './ProductImage.vue'
import StockStamp from './StockStamp.vue'

defineProps<{ product: Product }>()
</script>

<template>
  <article class="card">
    <RouterLink :to="`/products/${product.id}`" class="link">
      <div class="media">
        <ProductImage :name="product.name" :color="product.image_color" />
        <StockStamp class="stamp" :stock="product.stock" />
      </div>
      <h3 class="name">{{ product.name }}</h3>
      <p class="price">{{ formatPrice(product.price) }}</p>
    </RouterLink>
  </article>
</template>

<style scoped>
.card {
  background: var(--color-surface);
  border: 1px solid var(--color-line);
  border-radius: var(--radius-lg);
  padding: var(--space-3);
}
.card:hover {
  border-color: var(--color-ink);
}
.link {
  color: inherit;
  text-decoration: none;
  display: block;
}
.media {
  position: relative;
}
.stamp {
  position: absolute;
  right: var(--space-2);
  bottom: var(--space-2);
}
.name {
  font-family: var(--font-body);
  font-size: var(--text-base);
  font-weight: 600;
  margin: var(--space-3) 0 0;
}
.price {
  margin: 0;
}
</style>
