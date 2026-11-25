<!-- 商品篩選：關鍵字、分類、價格區間、排序。按「套用」才送出。 -->
<script setup lang="ts">
import { reactive, watch } from 'vue'
import type { Category, ProductSort } from '@/api/types'

export interface Filters {
  q: string
  category_id: number | null
  min_price: number | null
  max_price: number | null
  sort: ProductSort
}

const props = defineProps<{ categories: Category[]; modelValue: Filters }>()
const emit = defineEmits<{ apply: [filters: Filters] }>()
const form = reactive<Filters>({ ...props.modelValue })
watch(
  () => props.modelValue,
  (v) => Object.assign(form, v),
)

// 【可修改】排序選項的中文名稱（值必須是後端白名單中的 newest／price_asc／price_desc／name）
const sortOptions: { value: ProductSort; label: string }[] = [
  { value: 'newest', label: '最新上架' },
  { value: 'price_asc', label: '價格低到高' },
  { value: 'price_desc', label: '價格高到低' },
  { value: 'name', label: '名稱' },
]
</script>

<template>
  <form class="filters" @submit.prevent="emit('apply', { ...form })">
    <div class="field">
      <label for="f-q">關鍵字</label>
      <input id="f-q" v-model.trim="form.q" type="search" maxlength="50" />
    </div>
    <div class="field">
      <label for="f-cat">分類</label>
      <select id="f-cat" v-model="form.category_id">
        <option :value="null">全部</option>
        <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
      </select>
    </div>
    <div class="field">
      <label for="f-min">最低價</label>
      <input id="f-min" v-model.number="form.min_price" type="number" min="0" inputmode="numeric" />
    </div>
    <div class="field">
      <label for="f-max">最高價</label>
      <input id="f-max" v-model.number="form.max_price" type="number" min="0" inputmode="numeric" />
    </div>
    <div class="field">
      <label for="f-sort">排序</label>
      <select id="f-sort" v-model="form.sort">
        <option v-for="o in sortOptions" :key="o.value" :value="o.value">{{ o.label }}</option>
      </select>
    </div>
    <button type="submit" class="btn">套用</button>
  </form>
</template>

<style scoped>
.filters {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr 1fr auto;
  gap: var(--space-3);
  align-items: end;
  margin-bottom: var(--space-5);
}
.field {
  margin: 0;
}
@media (max-width: 800px) {
  .filters {
    grid-template-columns: 1fr 1fr;
  }
}
</style>
