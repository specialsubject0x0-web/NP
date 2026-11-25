<!-- 金額明細（小計、折扣、運費、總計）。金額來自後端試算或訂單，這個元件只負責顯示。 -->
<script setup lang="ts">
import { formatPrice } from '@/composables/format'

defineProps<{
  subtotal: number
  discount: number
  shippingFee: number
  total: number
  couponCode?: string | null
}>()
</script>

<template>
  <dl class="summary">
    <div>
      <dt>商品小計</dt>
      <dd>{{ formatPrice(subtotal) }}</dd>
    </div>
    <div v-if="discount > 0">
      <dt>
        優惠折抵<span v-if="couponCode">（{{ couponCode }}）</span>
      </dt>
      <dd>−{{ formatPrice(discount) }}</dd>
    </div>
    <div>
      <dt>運費</dt>
      <dd>{{ shippingFee === 0 ? '免運' : formatPrice(shippingFee) }}</dd>
    </div>
    <div class="total">
      <dt>總計</dt>
      <dd class="price">{{ formatPrice(total) }}</dd>
    </div>
  </dl>
</template>

<style scoped>
.summary {
  margin: 0;
}
.summary div {
  display: flex;
  justify-content: space-between;
  padding: var(--space-2) 0;
  border-bottom: 1px dashed var(--color-line);
}
dd {
  margin: 0;
  font-variant-numeric: tabular-nums;
}
.total {
  border-bottom: 0 !important;
  font-size: var(--text-lg);
  font-weight: 700;
}
</style>
