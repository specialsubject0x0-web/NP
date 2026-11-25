<!-- 我的訂單列表（US-007）。只會看到自己的訂單（後端保證）。 -->
<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { fetchOrders } from '@/api/orders'
import type { OrderSummary, Page } from '@/api/types'
import ErrorMessage from '@/components/ErrorMessage.vue'
import OrderStatusBadge from '@/components/OrderStatusBadge.vue'
import PaginationNav from '@/components/PaginationNav.vue'
import { formatDate, formatPrice } from '@/composables/format'

const result = ref<Page<OrderSummary> | null>(null)
const error = ref<string | null>(null)

async function load(page = 1): Promise<void> {
  try {
    result.value = await fetchOrders(page)
  } catch (e) {
    error.value = (e as Error).message
  }
}
onMounted(() => load())
</script>

<template>
  <div class="page">
    <h1>我的訂單</h1>
    <ErrorMessage :message="error" />
    <template v-if="result">
      <p v-if="result.items.length === 0">還沒有訂單。<RouterLink to="/products">去逛逛</RouterLink></p>
      <table v-else class="table">
        <thead>
          <tr>
            <th>訂單編號</th>
            <th>下單時間</th>
            <th>件數</th>
            <th class="num">金額</th>
            <th>狀態</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="o in result.items" :key="o.id">
            <td>
              <RouterLink :to="`/orders/${o.id}`">#{{ o.id }}</RouterLink>
            </td>
            <td>{{ formatDate(o.created_at) }}</td>
            <td>{{ o.item_count }}</td>
            <td class="num">{{ formatPrice(o.total) }}</td>
            <td><OrderStatusBadge :status="o.status" /></td>
          </tr>
        </tbody>
      </table>
      <PaginationNav :page="result.page" :page-size="result.page_size" :total="result.total" @change="load" />
    </template>
  </div>
</template>
