<!-- 後台的分頁切換。 -->
<template>
  <nav class="admin-nav" aria-label="後台">
    <RouterLink to="/admin/products">商品管理</RouterLink>
    <RouterLink to="/admin/orders">訂單管理</RouterLink>
  </nav>
</template>

<style scoped>
.admin-nav {
  display: flex;
  gap: var(--space-4);
  margin-bottom: var(--space-5);
  border-bottom: 1px solid var(--color-line);
}
a {
  padding: var(--space-2) 0;
  text-decoration: none;
}
a.router-link-active {
  border-bottom: 3px solid var(--color-ink);
  font-weight: 700;
}
</style>
