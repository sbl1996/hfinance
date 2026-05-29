import { createRouter, createWebHistory } from 'vue-router'
import { isGuestToken } from '@/utils/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/AuthView.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/',
    redirect: '/assets',
  },
  {
    path: '/dashboard',
    redirect: '/assets',
  },
  {
    path: '/accounting',
    redirect: '/assets',
  },
  {
    path: '/assets',
    name: 'Assets',
    component: () => import('@/views/AssetsView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/investment',
    name: 'Investment',
    component: () => import('@/views/InvestmentView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/investment/:id',
    name: 'HoldingDetail',
    component: () => import('@/views/HoldingDetailView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/watchlist/:id',
    name: 'WatchlistDetail',
    component: () => import('@/views/WatchlistDetailView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/tasks',
    name: 'FetchTasks',
    component: () => import('@/views/FetchTaskListView.vue'),
    meta: { requiresAuth: true, adminOnly: true },
  },
  {
    path: '/tasks/:id',
    name: 'FetchTaskDetail',
    component: () => import('@/views/FetchTaskDetailView.vue'),
    meta: { requiresAuth: true, adminOnly: true },
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/views/ProfileView.vue'),
    meta: { requiresAuth: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 全局路由守卫 - 认证检查
router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('token')
  if (to.meta.requiresAuth !== false && !token) {
    next({ name: 'Login' })
  } else if (to.name === 'Login' && token) {
    next({ name: 'Assets' })
  } else if (to.meta.adminOnly && isGuestToken(token)) {
    next({ name: 'Assets' })
  } else {
    next()
  }
})

export default router
