import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/pages/Login.vue'),
    meta: { requiresAuth: false, title: '登录' }
  },
  {
    path: '/',
    component: () => import('@/layout/MainLayout.vue'),
    meta: { requiresAuth: true },
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/pages/Dashboard.vue'),
        meta: { title: '首页', icon: 'HomeOutlined', roles: ['admin', 'employee', 'supervisor'] }
      },
      {
        path: 'knowledge',
        name: 'Knowledge',
        component: () => import('@/pages/KnowledgeList.vue'),
        meta: { title: '制度条目', icon: 'BookOutlined', roles: ['admin', 'employee', 'supervisor'] }
      },
      {
        path: 'my-knowledge',
        name: 'MyKnowledge',
        component: () => import('@/pages/MyKnowledge.vue'),
        meta: { title: '我的提交', icon: 'FileTextOutlined', roles: ['employee', 'supervisor'] }
      },
      {
        path: 'reading',
        name: 'Reading',
        component: () => import('@/pages/ReadingStatus.vue'),
        meta: { title: '阅读确认', icon: 'ReadOutlined', roles: ['admin', 'employee', 'supervisor'] }
      },
      {
        path: 'review',
        name: 'Review',
        component: () => import('@/pages/ReviewList.vue'),
        meta: { title: '到期复核', icon: 'AuditOutlined', roles: ['supervisor'] }
      },
      {
        path: 'categories',
        name: 'Categories',
        component: () => import('@/pages/CategoryManagement.vue'),
        meta: { title: '制度目录', icon: 'FolderOutlined', roles: ['admin'] }
      },
      {
        path: 'groups',
        name: 'Groups',
        component: () => import('@/pages/GroupManagement.vue'),
        meta: { title: '责任小组', icon: 'TeamOutlined', roles: ['admin'] }
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/pages/NotFound.vue'),
    meta: { requiresAuth: false }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to, from, next) => {
  const userStore = useUserStore()
  userStore.loadUserFromStorage()

  if (to.meta.requiresAuth) {
    if (!userStore.token) {
      next({ path: '/login', query: { redirect: to.fullPath } })
      return
    }
    if (!userStore.user) {
      await userStore.fetchCurrentUser()
    }
    if (to.meta.roles && userStore.user) {
      const roles = to.meta.roles as string[]
      if (!roles.includes(userStore.user.role)) {
        next('/dashboard')
        return
      }
    }
  }

  if (to.path === '/login' && userStore.token) {
    next('/dashboard')
    return
  }

  document.title = to.meta.title ? `${to.meta.title} - 企业制度知识复核与阅读追踪系统` : '企业制度知识复核与阅读追踪系统'
  next()
})

export default router
