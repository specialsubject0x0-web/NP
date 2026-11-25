<!--
  首頁。文案在 content/home.json（【手動修改區】）；要不要顯示精選商品、分類捷徑，在 config/site.config.ts 設定。
-->
<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { fetchCategories, fetchProducts } from '@/api/products'
import type { Category, Product } from '@/api/types'
import ProductGrid from '@/components/ProductGrid.vue'
import ProductImage from '@/components/ProductImage.vue'
import { siteConfig } from '@/config/site.config'
import home from '@/content/home.json'

const featured = ref<Product[]>([])
const signs = ref<Product[]>([])
const categories = ref<Category[]>([])

onMounted(async () => {
  const [products, cats] = await Promise.all([
    // 多拿 3 個：前 3 個做成大標旁的招牌，其餘放在精選區（兩邊不重複）
    fetchProducts({ page_size: siteConfig.featuredCount + 3, sort: 'newest' }),
    fetchCategories(),
  ]).catch(() => [null, []] as const)
  signs.value = products?.items.slice(0, 3) ?? []
  featured.value = products?.items.slice(3) ?? []
  categories.value = [...cats]
})
</script>

<template>
  <div class="page">
    <section class="hero">
      <div class="hero-text">
        <h1 class="hero-title">{{ home.heroTitle }}</h1>
        <p class="hero-lead">{{ home.heroText }}</p>
        <RouterLink to="/products" class="btn">{{ home.heroButton }}</RouterLink>
      </div>
      <!-- 三個商品排成錯落的「招牌」 -->
      <div class="hero-signs" aria-hidden="true">
        <ProductImage v-for="p in signs" :key="p.id" :name="p.name" :color="p.image_color" />
      </div>
    </section>

    <p class="notice">{{ home.notice }}</p>

    <section v-if="siteConfig.showCategoriesOnHome && categories.length" class="block">
      <h2>{{ home.categoriesTitle }}</h2>
      <ul class="cats">
        <li v-for="c in categories" :key="c.id">
          <RouterLink :to="{ name: 'products', query: { category_id: c.id } }">{{ c.name }}</RouterLink>
        </li>
      </ul>
    </section>

    <section v-if="siteConfig.showFeaturedOnHome && featured.length" class="block">
      <h2>{{ home.featuredTitle }}</h2>
      <ProductGrid :products="featured" />
    </section>
  </div>
</template>

<style scoped>
.hero {
  display: grid;
  grid-template-columns: 1.1fr 1fr;
  gap: var(--space-6);
  align-items: center;
  padding: var(--space-6) 0;
}
.hero-title {
  font-size: var(--text-hero);
  letter-spacing: 0.12em;
  color: var(--color-ink);
  margin-bottom: var(--space-4);
}
.hero-lead {
  font-size: var(--text-lg);
  max-width: 28em;
  margin: 0 0 var(--space-5);
}
/* 三塊招牌錯落排列：這是首頁唯一的「裝飾」 */
.hero-signs {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-3);
}
.hero-signs > :nth-child(2) {
  transform: translateY(var(--space-6));
}
.notice {
  border-top: 2px solid var(--color-ink);
  border-bottom: 1px solid var(--color-line);
  padding: var(--space-3) 0;
  margin: var(--space-6) 0 var(--space-5);
  font-weight: 600;
}
.block {
  margin-top: var(--space-6);
}
.cats {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
}
.cats a {
  display: inline-block;
  padding: var(--space-2) var(--space-5);
  border: 1px solid var(--color-ink);
  border-radius: var(--radius);
  text-decoration: none;
  font-family: var(--font-display);
  font-size: var(--text-lg);
  background: var(--color-surface);
}
.cats a:hover {
  background: var(--color-ink-soft);
}
@media (max-width: 760px) {
  .hero {
    grid-template-columns: 1fr;
    padding: var(--space-5) 0;
  }
  .hero-signs > :nth-child(2) {
    transform: none;
  }
}
</style>
