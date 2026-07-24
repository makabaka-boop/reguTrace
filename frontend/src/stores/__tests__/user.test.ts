/**
 * 用户状态 store 测试：登录状态更新、token/user 持久化、权限判断、异常处理。
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

// mock 认证接口，控制返回值
const apiLogin = vi.fn()
const apiLogout = vi.fn(() => Promise.resolve({ code: 200 }))
const getCurrentUser = vi.fn()

vi.mock('@/api/auth', () => ({
  login: (...args: any[]) => apiLogin(...args),
  logout: (...args: any[]) => apiLogout(...args),
  getCurrentUser: (...args: any[]) => getCurrentUser(...args),
}))

import { useUserStore } from '@/stores/user'
import { message } from 'ant-design-vue'

beforeEach(() => {
  setActivePinia(createPinia())
  localStorage.clear()
  vi.clearAllMocks()
})

describe('useUserStore - login', () => {
  it('登录成功时更新 user/token 并写入 localStorage', async () => {
    apiLogin.mockResolvedValue({
      code: 200,
      data: { id: 1, username: 'emp', role: 'employee', name: '张三', token: 'tok', created_at: '2026-01-01' },
    })
    const store = useUserStore()
    const ok = await store.login({ username: 'emp', password: 'p', role: 'employee' })

    expect(ok).toBe(true)
    expect(store.user?.name).toBe('张三')
    expect(store.token).toBe('tok')
    expect(store.isLogin).toBe(true)
    expect(localStorage.getItem('token')).toBe('tok')
    expect(JSON.parse(localStorage.getItem('user')!).username).toBe('emp')
    expect(message.success).toHaveBeenCalled()
  })

  it('登录返回非 200 时返回 false 且不设置用户', async () => {
    apiLogin.mockResolvedValue({ code: 401, data: null })
    const store = useUserStore()
    const ok = await store.login({ username: 'x', password: 'y', role: 'employee' })
    expect(ok).toBe(false)
    expect(store.user).toBeNull()
    expect(store.isLogin).toBe(false)
  })

  it('登录抛异常时捕获并返回 false', async () => {
    apiLogin.mockRejectedValue(new Error('network'))
    const store = useUserStore()
    const ok = await store.login({ username: 'x', password: 'y', role: 'employee' })
    expect(ok).toBe(false)
  })
})

describe('useUserStore - token/user 管理', () => {
  it('setToken(null) 清空 token 与 user 存储', () => {
    const store = useUserStore()
    store.setToken('abc')
    expect(localStorage.getItem('token')).toBe('abc')
    store.setToken(null)
    expect(localStorage.getItem('token')).toBeNull()
    expect(localStorage.getItem('user')).toBeNull()
  })

  it('loadUserFromStorage 从本地恢复用户', () => {
    localStorage.setItem('user', JSON.stringify({ id: 2, username: 'sup', role: 'supervisor', name: '李四', created_at: '' }))
    const store = useUserStore()
    store.loadUserFromStorage()
    expect(store.user?.username).toBe('sup')
  })

  it('loadUserFromStorage 解析异常时不抛错', () => {
    localStorage.setItem('user', '{invalid json')
    const store = useUserStore()
    expect(() => store.loadUserFromStorage()).not.toThrow()
    expect(store.user).toBeNull()
  })
})

describe('useUserStore - hasRole 权限判断', () => {
  it('未登录时返回 false', () => {
    const store = useUserStore()
    expect(store.hasRole('admin')).toBe(false)
  })

  it('单角色匹配', () => {
    const store = useUserStore()
    store.setUser({ id: 1, username: 'a', role: 'admin', name: 'A', created_at: '' } as any)
    expect(store.hasRole('admin')).toBe(true)
    expect(store.hasRole('employee')).toBe(false)
  })

  it('角色数组匹配', () => {
    const store = useUserStore()
    store.setUser({ id: 1, username: 's', role: 'supervisor', name: 'S', created_at: '' } as any)
    expect(store.hasRole(['admin', 'supervisor'])).toBe(true)
    expect(store.hasRole(['admin', 'employee'])).toBe(false)
  })

  it('userRole/userName 计算属性反映当前用户', () => {
    const store = useUserStore()
    store.setUser({ id: 1, username: 'e', role: 'employee', name: '员工', created_at: '' } as any)
    expect(store.userRole).toBe('employee')
    expect(store.userName).toBe('员工')
  })
})

describe('useUserStore - fetchCurrentUser', () => {
  it('成功时刷新 user', async () => {
    getCurrentUser.mockResolvedValue({
      code: 200,
      data: { id: 3, username: 'admin', role: 'admin', name: '管理员', created_at: '' },
    })
    const store = useUserStore()
    const u = await store.fetchCurrentUser()
    expect(u?.username).toBe('admin')
  })

  it('异常时清空登录态', async () => {
    getCurrentUser.mockRejectedValue(new Error('401'))
    const store = useUserStore()
    store.setToken('tok')
    const u = await store.fetchCurrentUser()
    expect(u).toBeNull()
    expect(store.token).toBeNull()
    expect(store.user).toBeNull()
  })
})

describe('useUserStore - logout', () => {
  it('登出后清空状态并跳转', async () => {
    const store = useUserStore()
    store.setToken('tok')
    store.setUser({ id: 1, username: 'a', role: 'admin', name: 'A', created_at: '' } as any)
    await store.logout()
    expect(store.token).toBeNull()
    expect(store.user).toBeNull()
    expect(apiLogout).toHaveBeenCalled()
  })
})
