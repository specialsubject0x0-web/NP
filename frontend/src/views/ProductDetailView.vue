<!-- 商品詳情：大圖、價格、庫存、說明、加入購物車（US-002、US-003）。沒登入按加入購物車會先帶去登入。 -->
<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ApiError } from '@/api/client'
import { fetchProduct } from '@/api/products'
import type { Product } from '@/api/types'
import ErrorMessage from '@/components/ErrorMessage.vue'
import ProductImage from '@/components/ProductImage.vue'
import QuantityInput from '@/components/QuantityInput.vue'
import StockStamp from '@/components/StockStamp.vue'
import { formatPrice } from '@/composables/format'
import { useAuthStore } from '@/stores/auth'
import { useCartStore } from '@/stores/cart'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const cart = useCartStore()

const product = ref<Product | null>(null)
const notFound = ref(false)
const quantity = ref(1)
const error = ref<string | null>(null)
const added = ref(false)
const busy = ref(false)

onMounted(async () => {
  try {
    product.value = await fetchProduct(Number(route.params.id))
  } catch (e) {
    if (e instanceof ApiError && e.status === 404) notFound.value = true
    else error.value = (e as Error).message
  }
})

async function addToCart(): Promise<void> {
  if (!product.value) return
  if (!auth.isLoggedIn) {
    void router.push({ name: 'login', query: { redirect: route.fullPath } })
    return
  }
  error.value = null
  added.value = false
  busy.value = true
  try {
    await cart.add(product.value.id, quantity.value)
    added.value = true
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div class="page">
    <div v-if="notFound">
      <h1>找不到這個商品</h1>
      <p>商品可能已經下架。<RouterLink to="/products">回到商品列表</RouterLink></p>
    </div>
    <article v-else-if="product" class="detail">
      <ProductImage :name="product.name" :color="product.image_color" size="lg" />
      <div class="info">
        <h1>{{ product.name }}</h1>
        <p class="price big">{{ formatPrice(product.price) }}</p>
        <p>{{ product.description }}</p>
        <p class="stock">
          <span class="muted">庫存 {{ product.stock }} 件</span>
          <StockStamp :stock="product.stock" />
        </p>
        <div v-if="product.stock > 0" class="buy">
          <QuantityInput v-model="quantity" :max="product.stock" />
          <button class="btn" :disabled="busy" @click="addToCart">加入購物車</button>
        </div>
        <p v-if="added" class="ok" role="status">已加入購物車。<RouterLink to="/cart">去結帳</RouterLink></p>
        <ErrorMessage :message="error" />
      </div>
    </article>
  </div>
</template>

<style scoped>
.detail {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-6);
  align-items: start;
}
.big {
  font-size: var(--text-xl);
  margin: 0 0 var(--space-4);
}
.info p {
  max-width: 34em;
}
.stock {
  display: flex;
  gap: var(--space-3);
  align-items: center;
}
.buy {
  display: flex;
  gap: var(--space-3);
  margin: var(--space-5) 0;
}
.ok {
  color: var(--color-ok);
  font-weight: 600;
}
@media (max-width: 760px) {
  .detail {
    grid-template-columns: 1fr;
  }
}
</style>
