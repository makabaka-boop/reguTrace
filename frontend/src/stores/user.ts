import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User, UserRole } from '@/types'
import { login as apiLogin, logout as apiLogout, getCurrentUser } from '@/api/auth'
import type { LoginParams } from '@/api/auth'
import { message } from 'ant-design-vue'
import router from '@/router'

export const useUserStore = defineStore('user', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('token'))

  const isLogin = computed(() => !!token.value && !!user.value)
  const userRole = computed(() => user.value?.role || null)
  const userName = computed(() => user.value?.name || '')

  const setToken = (t: string | null) => {
    token.value = t
    if (t) {
      localStorage.setItem('token', t)
    } else {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    }
  }

  const setUser = (u: User | null) => {
    user.value = u
    if (u) {
      localStorage.setItem('user', JSON.stringify(u))
    } else {
      localStorage.removeItem('user')
    }
  }

  const loadUserFromStorage = () => {
    const stored = localStorage.getItem('user')
    if (stored) {
      try {
        user.value = JSON.parse(stored)
      } catch (e) {
        console.error('Failed to parse user from storage:', e)
      }
    }
  }

  const login = async (params: LoginParams) => {
    try {
      const res = await apiLogin(params)
      if (res.code === 200 && res.data) {
        const userData = {
          id: res.data.id,
          username: res.data.username,
          role: res.data.role as UserRole,
          name: res.data.name,
          created_at: res.data.created_at
        }
        setToken(res.data.token || '')
        setUser(userData)
        message.success(`登录成功，欢迎 ${userData.name}！`)
        return true
      }
      return false
    } catch (error) {
      console.error('Login error:', error)
      return false
    }
  }

  const logout = async () => {
    try {
      await apiLogout()
    } catch (e) {
      console.error('Logout error:', e)
    } finally {
      setToken(null)
      setUser(null)
      message.info('已退出登录')
      router.push('/login')
    }
  }

  const fetchCurrentUser = async () => {
    try {
      const res = await getCurrentUser()
      if (res.code === 200 && res.data) {
        setUser({
          id: res.data.id,
          username: res.data.username,
          role: res.data.role as UserRole,
          name: res.data.name,
          created_at: res.data.created_at
        })
        return user.value
      }
      return null
    } catch (error) {
      setToken(null)
      setUser(null)
      return null
    }
  }

  const hasRole = (roles: UserRole | UserRole[]) => {
    if (!user.value) return false
    if (Array.isArray(roles)) {
      return roles.includes(user.value.role)
    }
    return user.value.role === roles
  }

  return {
    user,
    token,
    isLogin,
    userRole,
    userName,
    login,
    logout,
    setToken,
    setUser,
    loadUserFromStorage,
    fetchCurrentUser,
    hasRole
  }
})
