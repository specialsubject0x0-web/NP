// 路由：網址 → 頁面。一個網址對應 views/ 裡的一個檔案。
// meta.requiresAuth：需要登入；meta.requiresAdmin：需要管理員。
// 【重要】這裡的檢查只是「體驗」（沒登入就帶去登入頁）；真正的權限由後端檢查。
import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

export const routes: RouteRecordRaw[] = [
  { path: '/', name: 'home', component: () => import('@/views/HomeView.vue') },
  { path: '/products', name: 'products', component: () => import('@/views/ProductListView.vue') },
  { path: '/products/:id(\\d+)', name: 'product', component: () => import('@/views/ProductDetailView.vue') },
  {
    path: '/cart',
    name: 'cart',
    component: () => import('@/views/CartView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/checkout',
    name: 'checkout',
    component: () => import('@/views/CheckoutView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/orders',
    name: 'orders',
    component: () => import('@/views/OrderListView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/orders/:id(\\d+)',
    name: 'order',
    component: () => import('@/views/OrderDetailView.vue'),
    meta: { requiresAuth: true },
  },
  { path: '/login', name: 'login', component: () => import('@/views/LoginView.vue') },
  { path: '/register', name: 'register', component: () => import('@/views/RegisterView.vue') },
  { path: '/faq', name: 'faq', component: () => import('@/views/FaqView.vue') },
  {
    path: '/admin/products',
    name: 'admin-products',
    component: () => import('@/views/admin/AdminProductsView.vue'),
    meta: { requiresAdmin: true },
  },
  {
    path: '/admin/orders',
    name: 'admin-orders',
    component: () => import('@/views/admin/AdminOrdersView.vue'),
    meta: { requiresAdmin: true },
  },
  { path: '/:pathMatch(.*)*', name: 'not-found', component: () => import('@/views/NotFoundView.vue') },
]

export function createAppRouter(history = createWebHistory()) {
  const router = createRouter({ history, routes, scrollBehavior: () => ({ top: 0 }) })

  router.beforeEach(async (to) => {
    const auth = useAuthStore()
    await auth.load()
    if ((to.meta.requiresAuth || to.meta.requiresAdmin) && !auth.isLoggedIn) {
      // 登入後回到原本想去的頁面
      return { name: 'login', query: { redirect: to.fullPath } }
    }
    if (to.meta.requiresAdmin && !auth.isAdmin) return { name: 'home' }
    return true
  })
  return router
}
