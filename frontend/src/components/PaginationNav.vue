<!-- 分頁：上一頁／下一頁與目前頁數。 -->
<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ page: number; pageSize: number; total: number }>()
const emit = defineEmits<{ change: [page: number] }>()
const pages = computed(() => Math.max(1, Math.ceil(props.total / props.pageSize)))
</script>

<template>
  <nav v-if="pages > 1" class="pager" aria-label="分頁">
    <button class="btn btn--ghost btn--small" :disabled="page <= 1" @click="emit('change', page - 1)">
      上一頁
    </button>
    <span>第 {{ page }} / {{ pages }} 頁</span>
    <button class="btn btn--ghost btn--small" :disabled="page >= pages" @click="emit('change', page + 1)">
      下一頁
    </button>
  </nav>
</template>

<style scoped>
.pager {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-4);
  margin-top: var(--space-5);
}
</style>
