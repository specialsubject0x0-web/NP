<!-- 訂單狀態標籤。中文名稱在 composables/format.ts 的 STATUS_LABELS（【可修改】）。 -->
<script setup lang="ts">
import type { OrderStatus } from '@/api/types'
import { STATUS_LABELS } from '@/composables/format'

defineProps<{ status: OrderStatus }>()
</script>

<template>
  <span class="badge" :class="`badge--${status}`">{{ STATUS_LABELS[status] }}</span>
</template>

<style scoped>
.badge {
  display: inline-block;
  padding: 0 var(--space-2);
  border-radius: 3px;
  font-size: var(--text-sm);
  font-weight: 600;
  border: 1px solid currentColor;
}
.badge--pending_payment {
  color: var(--color-seal);
}
.badge--paid,
.badge--shipped {
  color: var(--color-ink);
}
.badge--completed {
  color: var(--color-ok);
}
.badge--cancelled {
  color: var(--color-muted);
}
</style>
