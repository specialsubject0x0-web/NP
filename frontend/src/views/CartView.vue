<!--
  購物車（US-003）。這裡的小計只是參考；運費與優惠在結帳頁由後端計算。
-->
<script setup lang="ts">
import { onMounted, ref } from 'vue'
import ErrorMessage from '@/components/ErrorMessage.vue'
import ProductImage from '@/components/ProductImage.vue'
import QuantityInput from '@/components/QuantityInput.vue'
import { formatPrice } from '@/composables/format'
import { useCartStore } from '@/stores/cart'

const store = useCartStore()
const error = ref<string | null>(null)

async function run(action: () => Promise<void>): Promise<void> {
  error.value = null
  try {
    await action()
  } catch (e) {
    error.value = (e as Error).message
    await store.refresh().catch(() => undefined)
  }
}

onMounted(() => run(() => store.refresh()))
</script>

<template>
  <div class="page">
    <h1>購物車</h1>
    <ErrorMessage :message="error" />
    <template v-if="store.cart">
      <p v-if="store.cart.items.length === 0" class="empty">
        購物車是空的。<RouterLink to="/products">去逛逛</RouterLink>
      </p>
      <template v-else>
        <ul class="lines">
          <li v-for="item in store.cart.items" :key="item.product_id" class="line">
            <ProductImage class="thumb" :name="item.name" :color="item.image_color" size="sm" />
            <div class="name">
              <RouterLink :to="`/products/${item.product_id}`">{{ item.name }}</RouterLink>
              <div class="muted">{{ formatPrice(item.unit_price) }}／件</div>
              <div v-if="!item.is_available" class="warn">庫存不足或已下架，請調整數量或移除</div>
            </div>
            <QuantityInput
              :model-value="item.quantity"
              :max="Math.max(item.stock, 1)"
              :label="`${item.name} 數量`"
              @update:model-value="(q) => run(() => store.setQuantity(item.product_id, q))"
            />
            <div class="num line-total">{{ formatPrice(item.line_total) }}</div>
            <button class="btn btn--ghost btn--small" @click="run(() => store.remove(item.product_id))">
              移除
            </button>
          </li>
        </ul>
        <div class="foot">
          <p>
            商品小計 <strong class="price">{{ formatPrice(store.cart.subtotal) }}</strong><br />
            <span class="muted">運費與優惠在下一步計算</span>
          </p>
          <RouterLink to="/checkout" class="btn">前往結帳</RouterLink>
        </div>
      </template>
    </template>
  </div>
</template>

<style scoped>
.lines {
  list-style: none;
  padding: 0;
  margin: 0;
  background: var(--color-surface);
  border: 1px solid var(--color-line);
  border-radius: var(--radius-lg);
}
.line {
  display: grid;
  grid-template-columns: 64px 1fr auto 110px auto;
  gap: var(--space-4);
  align-items: center;
  padding: var(--space-3) var(--space-4);
  border-bottom: 1px solid var(--color-line);
}
.line:last-child {
  border-bottom: 0;
}
.warn {
  color: var(--color-error);
  font-size: var(--text-sm);
}
.line-total {
  text-align: right;
  font-variant-numeric: tabular-nums;
}
.foot {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: var(--space-5);
  margin-top: var(--space-5);
  text-align: right;
}
.empty {
  padding: var(--space-6) 0;
}
@media (max-width: 640px) {
  .line {
    grid-template-columns: 48px 1fr;
  }
}
</style>
