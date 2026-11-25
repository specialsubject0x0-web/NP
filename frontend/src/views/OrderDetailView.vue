<!--
  訂單詳情（US-006、US-007）：明細、金額、收件資訊；待付款時可以付款或取消。
  付款是模擬金流（人決定），不會要你輸入卡號。
-->
<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ApiError, newIdempotencyKey } from '@/api/client'
import { cancelOrder, fetchOrder, payOrder } from '@/api/orders'
import type { Order } from '@/api/types'
import ErrorMessage from '@/components/ErrorMessage.vue'
import OrderStatusBadge from '@/components/OrderStatusBadge.vue'
import PriceSummary from '@/components/PriceSummary.vue'
import { formatDate, formatPrice } from '@/composables/format'

const route = useRoute()
const order = ref<Order | null>(null)
const notFound = ref(false)
const error = ref<string | null>(null)
const message = ref<string | null>(route.query.created ? '訂單已成立，請完成付款。' : null)
const busy = ref(false)
// 同一次付款重試時沿用同一個 key，避免重複付款
const payKey = newIdempotencyKey()
const id = computed(() => Number(route.params.id))

async function load(): Promise<void> {
  try {
    order.value = await fetchOrder(id.value)
  } catch (e) {
    if (e instanceof ApiError && e.status === 404) notFound.value = true
    else error.value = (e as Error).message
  }
}

async function act(action: 'pay' | 'cancel'): Promise<void> {
  if (action === 'cancel' && !window.confirm('確定要取消這筆訂單嗎？')) return
  busy.value = true
  error.value = null
  try {
    if (action === 'pay') {
      await payOrder(id.value, payKey)
      message.value = '付款完成，我們會盡快出貨。'
    } else {
      await cancelOrder(id.value)
      message.value = '訂單已取消，商品已放回庫存。'
    }
    await load()
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    busy.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="page">
    <div v-if="notFound">
      <h1>找不到這筆訂單</h1>
      <p><RouterLink to="/orders">回到我的訂單</RouterLink></p>
    </div>
    <template v-else-if="order">
      <div class="head">
        <h1>訂單 #{{ order.id }}</h1>
        <OrderStatusBadge :status="order.status" />
      </div>
      <p class="muted">下單時間 {{ formatDate(order.created_at) }}</p>
      <p v-if="message" class="ok" role="status">{{ message }}</p>
      <ErrorMessage :message="error" />

      <div class="layout">
        <section class="panel">
          <h2>商品</h2>
          <table class="table">
            <thead>
              <tr>
                <th>商品</th>
                <th class="num">單價</th>
                <th class="num">數量</th>
                <th class="num">小計</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in order.items" :key="item.product_id">
                <td>{{ item.product_name }}</td>
                <td class="num">{{ formatPrice(item.unit_price) }}</td>
                <td class="num">{{ item.quantity }}</td>
                <td class="num">{{ formatPrice(item.line_total) }}</td>
              </tr>
            </tbody>
          </table>
          <h2 class="ship">收件資訊</h2>
          <p>{{ order.recipient_name }}　{{ order.recipient_phone }}<br />{{ order.shipping_address }}</p>
        </section>
        <aside class="panel">
          <PriceSummary
            :subtotal="order.subtotal"
            :discount="order.discount"
            :shipping-fee="order.shipping_fee"
            :total="order.total"
            :coupon-code="order.coupon_code"
          />
          <div v-if="order.status === 'pending_payment'" class="actions">
            <button class="btn" :disabled="busy" @click="act('pay')">付款（模擬）</button>
            <button class="btn btn--ghost" :disabled="busy" @click="act('cancel')">取消訂單</button>
          </div>
        </aside>
      </div>
    </template>
  </div>
</template>

<style scoped>
.head {
  display: flex;
  gap: var(--space-3);
  align-items: center;
}
.head h1 {
  margin: 0;
}
.ok {
  color: var(--color-ok);
  font-weight: 600;
}
.layout {
  display: grid;
  grid-template-columns: 1.6fr 1fr;
  gap: var(--space-5);
  align-items: start;
}
.ship {
  margin-top: var(--space-5);
}
.actions {
  display: grid;
  gap: var(--space-2);
  margin-top: var(--space-4);
}
@media (max-width: 760px) {
  .layout {
    grid-template-columns: 1fr;
  }
}
</style>
