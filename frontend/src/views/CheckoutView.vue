<!--
  結帳（US-005、US-011）：選地址 → 輸入優惠碼 → 後端試算 → 送出訂單。
  【重要】畫面上的金額全部來自後端試算（fetchQuote），前端不自己算運費或折扣。
  【重要】Idempotency-Key 在進入頁面時產生一次；連按兩次「送出訂單」也只會成立一筆訂單。
-->
<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { newIdempotencyKey } from '@/api/client'
import { createOrder, fetchQuote } from '@/api/orders'
import type { Quote } from '@/api/types'
import AddressPicker from '@/components/AddressPicker.vue'
import ErrorMessage from '@/components/ErrorMessage.vue'
import PriceSummary from '@/components/PriceSummary.vue'
import { formatPrice } from '@/composables/format'
import { useCartStore } from '@/stores/cart'

const router = useRouter()
const cart = useCartStore()
const quote = ref<Quote | null>(null)
const addressId = ref<number | null>(null)
const couponInput = ref('')
const appliedCoupon = ref<string | undefined>(undefined)
const error = ref<string | null>(null)
const couponError = ref<string | null>(null)
const submitting = ref(false)
const idempotencyKey = newIdempotencyKey()

async function loadQuote(): Promise<void> {
  try {
    quote.value = await fetchQuote(appliedCoupon.value)
  } catch (e) {
    quote.value = null
    error.value = (e as Error).message
  }
}

async function applyCoupon(): Promise<void> {
  couponError.value = null
  const code = couponInput.value.trim()
  try {
    quote.value = await fetchQuote(code || undefined)
    appliedCoupon.value = code || undefined
  } catch (e) {
    couponError.value = (e as Error).message
  }
}

async function removeCoupon(): Promise<void> {
  couponInput.value = ''
  appliedCoupon.value = undefined
  couponError.value = null
  await loadQuote()
}

async function submit(): Promise<void> {
  if (addressId.value === null || submitting.value) return
  submitting.value = true
  error.value = null
  try {
    const order = await createOrder(addressId.value, appliedCoupon.value, idempotencyKey)
    cart.clear()
    await cart.refresh().catch(() => undefined)
    void router.push({ name: 'order', params: { id: order.id }, query: { created: '1' } })
  } catch (e) {
    error.value = (e as Error).message
    submitting.value = false
  }
}

onMounted(loadQuote)
</script>

<template>
  <div class="page">
    <h1>結帳</h1>
    <ErrorMessage :message="error" />
    <p v-if="!quote && error"><RouterLink to="/cart">回購物車調整</RouterLink></p>
    <div v-if="quote" class="layout">
      <div>
        <AddressPicker v-model="addressId" />

        <form class="coupon" @submit.prevent="applyCoupon">
          <div class="field">
            <label for="coupon">優惠碼（一次限用一張）</label>
            <input id="coupon" v-model="couponInput" maxlength="32" autocomplete="off" />
          </div>
          <button type="submit" class="btn btn--ghost">套用</button>
          <button v-if="appliedCoupon" type="button" class="btn btn--ghost" @click="removeCoupon">
            不使用
          </button>
        </form>
        <ErrorMessage :message="couponError" />
      </div>

      <aside class="panel">
        <h2>訂單明細</h2>
        <ul class="items">
          <li v-for="line in quote.items" :key="line.product_id">
            <span>{{ line.name }} × {{ line.quantity }}</span>
            <span class="num">{{ formatPrice(line.line_total) }}</span>
          </li>
        </ul>
        <PriceSummary
          :subtotal="quote.subtotal"
          :discount="quote.discount"
          :shipping-fee="quote.shipping_fee"
          :total="quote.total"
          :coupon-code="quote.coupon_code"
        />
        <button class="btn submit" :disabled="addressId === null || submitting" @click="submit">
          {{ submitting ? '送出中…' : '送出訂單' }}
        </button>
        <p class="muted small">送出後訂單為「待付款」，可在下一頁付款。</p>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.layout {
  display: grid;
  grid-template-columns: 1.3fr 1fr;
  gap: var(--space-6);
  align-items: start;
}
.coupon {
  display: flex;
  gap: var(--space-2);
  align-items: end;
}
.coupon .field {
  flex: 1;
  margin: 0;
}
.items {
  list-style: none;
  padding: 0;
  margin: 0 0 var(--space-3);
}
.items li {
  display: flex;
  justify-content: space-between;
  gap: var(--space-3);
  padding: var(--space-1) 0;
}
.submit {
  width: 100%;
  margin-top: var(--space-4);
}
.small {
  font-size: var(--text-sm);
}
@media (max-width: 760px) {
  .layout {
    grid-template-columns: 1fr;
  }
}
</style>
