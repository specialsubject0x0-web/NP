<!--
  商品列表：搜尋、篩選、排序、分頁（US-001）。篩選條件放在網址上，可以分享或重新整理不消失。
  每頁幾個由 config/site.config.ts 的 productsPerPage 決定。
-->
<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ApiError } from '@/api/client'
import { fetchCategories, fetchProducts } from '@/api/products'
import type { Category, Page, Product, ProductSort } from '@/api/types'
import ErrorMessage from '@/components/ErrorMessage.vue'
import PaginationNav from '@/components/PaginationNav.vue'
import ProductFilters, { type Filters } from '@/components/ProductFilters.vue'
import ProductGrid from '@/components/ProductGrid.vue'
import { siteConfig } from '@/config/site.config'

const route = useRoute()
const router = useRouter()
const categories = ref<Category[]>([])
const result = ref<Page<Product> | null>(null)
const error = ref<string | null>(null)
const loading = ref(false)

const num = (v: unknown): number | null =>
  v === undefined || v === '' || Number.isNaN(Number(v)) ? null : Number(v)

// 從網址讀出目前的篩選條件
const filters = computed<Filters>(() => ({
  q: String(route.query.q ?? ''),
  category_id: num(route.query.category_id),
  min_price: num(route.query.min_price),
  max_price: num(route.query.max_price),
  sort: (route.query.sort as ProductSort) || 'newest',
}))
const page = computed(() => num(route.query.page) ?? 1)

async function load(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    const f = filters.value
    result.value = await fetchProducts({
      q: f.q || undefined,
      category_id: f.category_id ?? undefined,
      min_price: f.min_price ?? undefined,
      max_price: f.max_price ?? undefined,
      sort: f.sort,
      page: page.value,
      page_size: siteConfig.productsPerPage,
    })
  } catch (e) {
    result.value = null
    error.value =
      e instanceof ApiError && e.status === 422 && e.code !== 'VALIDATION_ERROR'
        ? e.message
        : '搜尋條件有誤，請調整後再試'
  } finally {
    loading.value = false
  }
}

function apply(f: Filters, newPage = 1): void {
  const query: Record<string, string> = {}
  if (f.q) query.q = f.q
  if (f.category_id !== null) query.category_id = String(f.category_id)
  if (f.min_price !== null && String(f.min_price) !== '') query.min_price = String(f.min_price)
  if (f.max_price !== null && String(f.max_price) !== '') query.max_price = String(f.max_price)
  if (f.sort !== 'newest') query.sort = f.sort
  if (newPage > 1) query.page = String(newPage)
  void router.push({ name: 'products', query })
}

watch(() => route.query, load)
onMounted(async () => {
  categories.value = await fetchCategories().catch(() => [])
  await load()
})
</script>

<template>
  <div class="page">
    <h1>全部商品</h1>
    <ProductFilters :categories="categories" :model-value="filters" @apply="apply" />
    <ErrorMessage :message="error" />
    <p v-if="result" class="muted" aria-live="polite">共 {{ result.total }} 件商品</p>
    <ProductGrid v-if="result?.items.length" :products="result.items" />
    <p v-else-if="result && !loading" class="empty">
      找不到符合條件的商品。試試其他關鍵字，或<RouterLink to="/products">看全部商品</RouterLink>。
    </p>
    <PaginationNav
      v-if="result"
      :page="result.page"
      :page-size="result.page_size"
      :total="result.total"
      @change="(p) => apply(filters, p)"
    />
  </div>
</template>

<style scoped>
.empty {
  padding: var(--space-6) 0;
}
</style>
