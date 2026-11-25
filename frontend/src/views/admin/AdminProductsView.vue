<!--
  後台：商品管理（US-009）。可以改價格、庫存、上下架，也可以新增商品。
  【重要】改價只影響之後的新訂單；舊訂單保留下單當時的價格（R-07）。權限由後端檢查（R-14）。
-->
<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { createProduct, fetchAdminProducts, updateProduct } from '@/api/admin'
import { fetchCategories } from '@/api/products'
import type { AdminProduct, Category, ProductCreate } from '@/api/types'
import ErrorMessage from '@/components/ErrorMessage.vue'
import AdminNav from './AdminNav.vue'

const products = ref<AdminProduct[]>([])
const categories = ref<Category[]>([])
const error = ref<string | null>(null)
const saved = ref<number | null>(null)
const draft = reactive<ProductCreate>({
  name: '',
  description: '',
  price: 0,
  stock: 0,
  category_id: 1,
  image_color: '#5b6b7a',
  is_active: true,
})

async function load(): Promise<void> {
  products.value = (await fetchAdminProducts()).items
}

async function save(p: AdminProduct): Promise<void> {
  error.value = null
  try {
    const updated = await updateProduct(p.id, {
      price: Number(p.price),
      stock: Number(p.stock),
      is_active: p.is_active,
    })
    Object.assign(p, updated)
    saved.value = p.id
  } catch (e) {
    error.value = `#${p.id}：${(e as Error).message}`
  }
}

async function add(): Promise<void> {
  error.value = null
  try {
    await createProduct({ ...draft, price: Number(draft.price), stock: Number(draft.stock) })
    Object.assign(draft, { name: '', description: '', price: 0, stock: 0 })
    await load()
  } catch (e) {
    error.value = (e as Error).message
  }
}

onMounted(async () => {
  try {
    categories.value = await fetchCategories()
    await load()
  } catch (e) {
    error.value = (e as Error).message
  }
})
</script>

<template>
  <div class="page">
    <h1>後台</h1>
    <AdminNav />
    <ErrorMessage :message="error" />
    <table class="table">
      <thead>
        <tr>
          <th>#</th>
          <th>商品</th>
          <th class="num">價格</th>
          <th class="num">庫存</th>
          <th>上架</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="p in products" :key="p.id" :class="{ off: !p.is_active }">
          <td>{{ p.id }}</td>
          <td>{{ p.name }}</td>
          <td class="num">
            <input v-model.number="p.price" type="number" min="0" :aria-label="`${p.name} 價格`" />
          </td>
          <td class="num">
            <input v-model.number="p.stock" type="number" min="0" :aria-label="`${p.name} 庫存`" />
          </td>
          <td><input v-model="p.is_active" type="checkbox" :aria-label="`${p.name} 上架`" /></td>
          <td>
            <button class="btn btn--small" @click="save(p)">儲存</button>
            <span v-if="saved === p.id" class="ok" role="status">已儲存</span>
          </td>
        </tr>
      </tbody>
    </table>

    <form class="panel add" @submit.prevent="add">
      <h2>新增商品</h2>
      <div class="field">
        <label for="n-name">名稱</label><input id="n-name" v-model="draft.name" required maxlength="100" />
      </div>
      <div class="field">
        <label for="n-cat">分類</label>
        <select id="n-cat" v-model="draft.category_id">
          <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
        </select>
      </div>
      <div class="field">
        <label for="n-price">價格（元）</label
        ><input id="n-price" v-model.number="draft.price" type="number" min="0" required />
      </div>
      <div class="field">
        <label for="n-stock">庫存</label
        ><input id="n-stock" v-model.number="draft.stock" type="number" min="0" required />
      </div>
      <div class="field">
        <label for="n-color">圖片底色</label><input id="n-color" v-model="draft.image_color" type="color" />
      </div>
      <div class="field wide">
        <label for="n-desc">說明</label
        ><textarea id="n-desc" v-model="draft.description" maxlength="2000" rows="2" />
      </div>
      <button type="submit" class="btn">新增商品</button>
    </form>
  </div>
</template>

<style scoped>
.table input[type='number'] {
  width: 6.5em;
  text-align: right;
  padding: var(--space-1);
  border: 1px solid var(--color-line);
  border-radius: var(--radius);
  font: inherit;
}
.off td {
  color: var(--color-muted);
}
.ok {
  margin-left: var(--space-2);
  color: var(--color-ok);
  font-size: var(--text-sm);
}
.add {
  margin-top: var(--space-6);
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 0 var(--space-3);
  align-items: end;
}
.add h2,
.wide {
  grid-column: 1 / -1;
}
@media (max-width: 760px) {
  .add {
    grid-template-columns: 1fr 1fr;
  }
}
</style>
