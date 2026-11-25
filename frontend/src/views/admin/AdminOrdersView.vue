<!--
  後台：訂單管理（US-010）。依狀態篩選；已付款 → 出貨 → 完成；待付款可以取消。
  按鈕只會顯示「狀態機允許」的動作；就算有人硬送，後端也會拒絕（R-08）。
-->
<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { fetchAdminOrders, transitionOrder } from '@/api/admin'
import type { AdminOrder, OrderStatus } from '@/api/types'
import ErrorMessage from '@/components/ErrorMessage.vue'
import OrderStatusBadge from '@/components/OrderStatusBadge.vue'
import { formatDate, formatPrice, STATUS_LABELS } from '@/composables/format'
import AdminNav from './AdminNav.vue'

type Action = 'shipped' | 'completed' | 'cancelled'
const NEXT: Partial<Record<OrderStatus, { to: Action; label: string }>> = {
  pending_payment: { to: 'cancelled', label: '取消' },
  paid: { to: 'shipped', label: '出貨' },
  shipped: { to: 'completed', label: '完成' },
}

const orders = ref<AdminOrder[]>([])
const status = ref<OrderStatus | ''>('')
const error = ref<string | null>(null)

async function load(): Promise<void> {
  try {
    orders.value = (await fetchAdminOrders(status.value || undefined)).items
  } catch (e) {
    error.value = (e as Error).message
  }
}

async function move(order: AdminOrder, to: Action): Promise<void> {
  error.value = null
  try {
    await transitionOrder(order.id, to)
    await load()
  } catch (e) {
    error.value = `#${order.id}：${(e as Error).message}`
  }
}

watch(status, load)
onMounted(load)
</script>

<template>
  <div class="page">
    <h1>後台</h1>
    <AdminNav />
    <div class="field filter">
      <label for="st">狀態</label>
      <select id="st" v-model="status">
        <option value="">全部</option>
        <option v-for="(label, key) in STATUS_LABELS" :key="key" :value="key">{{ label }}</option>
      </select>
    </div>
    <ErrorMessage :message="error" />
    <p v-if="orders.length === 0" class="muted">目前沒有符合的訂單。</p>
    <table v-else class="table">
      <thead>
        <tr>
          <th>#</th>
          <th>時間</th>
          <th>收件人</th>
          <th class="num">金額</th>
          <th>狀態</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="o in orders" :key="o.id">
          <td>{{ o.id }}</td>
          <td>{{ formatDate(o.created_at) }}</td>
          <td>{{ o.recipient_name }}</td>
          <td class="num">{{ formatPrice(o.total) }}</td>
          <td><OrderStatusBadge :status="o.status" /></td>
          <td>
            <button v-if="NEXT[o.status]" class="btn btn--small" @click="move(o, NEXT[o.status]!.to)">
              {{ NEXT[o.status]!.label }}
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.filter {
  max-width: 220px;
}
</style>
