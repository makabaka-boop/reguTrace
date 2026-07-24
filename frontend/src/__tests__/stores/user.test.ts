import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

const { mockLoginApi, mockLogoutApi, mockGetCurrentUserApi } = vi.hoisted(() => ({
  mockLoginApi: vi.fn(),
  mockLogoutApi: vi.fn(),
  mockGetCurrentUserApi: vi.fn(),
}))

vi.mock('@/api/auth', () => ({
  login: (...args: any[]) => mockLoginApi(...args),
  logout: (...args: any[]) => mockLogoutApi(...args),
  getCurrentUser: (...args: any[]) => mockGetCurrentUserApi(...args),
}))

vi.mock('ant-design-vue', () => ({
  message: {
    success: vi.fn(),
    error: vi.fn(),
    info: vi.fn(),
  },
}))

vi.mock('@/router', () => ({
  default: {
    push: vi.fn(),
  },
}))

import { useUserStore } from '@/stores/user'

describe('user store', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    setActivePinia(createPinia())
  })

  it('initial state is unauthenticated', () => {
    const store = useUserStore()
    expect(store.user).toBeNull()
    expect(store.isLogin).toBe(false)
    expect(store.userRole).toBeNull()
    expect(store.userName).toBe('')
  })

  it('setToken stores and persists token', () => {
    const store = useUserStore()
    store.setToken('my-token-123')
    expect(store.token).toBe('my-token-123')
    expect(localStorage.getItem('token')).toBe('my-token-123')
  })

  it('setToken with null clears storage', () => {
    const store = useUserStore()
    store.setToken('token')
    store.setToken(null)
    expect(store.token).toBeNull()
    expect(localStorage.getItem('token')).toBeNull()
  })

  it('setUser stores and persists user data', () => {
    const store = useUserStore()
    const userData = { id: 1, username: 'admin', role: 'admin' as const, name: '管理员', created_at: '2024-01-01' }
    store.setUser(userData)
    expect(store.user).toEqual(userData)
    expect(JSON.parse(localStorage.getItem('user')!)).toEqual(userData)
  })

  it('setUser with null clears storage', () => {
    const store = useUserStore()
    store.setUser({ id: 1, username: 'admin', role: 'admin', name: 'Admin', created_at: '' })
    store.setUser(null)
    expect(store.user).toBeNull()
    expect(localStorage.getItem('user')).toBeNull()
  })

  it('loadUserFromStorage parses saved user', () => {
    const userData = { id: 5, username: 'emp', role: 'employee' as const, name: '员工', created_at: '2024-01-01' }
    localStorage.setItem('user', JSON.stringify(userData))
    const store = useUserStore()
    store.loadUserFromStorage()
    expect(store.user).toEqual(userData)
  })

  it('loadUserFromStorage handles invalid JSON gracefully', () => {
    localStorage.setItem('user', 'not-valid-json{{{')
    const store = useUserStore()
    expect(() => store.loadUserFromStorage()).not.toThrow()
    expect(store.user).toBeNull()
  })

  it('login success updates state', async () => {
    const store = useUserStore()
    mockLoginApi.mockResolvedValue({
      code: 200,
      data: { id: 1, username: 'admin', role: 'admin', name: '管理员', token: 'jwt-token', created_at: '2024-01-01' },
    })

    const result = await store.login({ username: 'admin', password: 'pass', role: 'admin' })
    expect(result).toBe(true)
    expect(store.isLogin).toBe(true)
    expect(store.userRole).toBe('admin')
    expect(store.userName).toBe('管理员')
    expect(store.token).toBe('jwt-token')
  })

  it('login failure returns false', async () => {
    const store = useUserStore()
    mockLoginApi.mockRejectedValue(new Error('Unauthorized'))

    const result = await store.login({ username: 'wrong', password: 'wrong', role: 'admin' })
    expect(result).toBe(false)
    expect(store.isLogin).toBe(false)
  })

  it('login with non-200 code returns false', async () => {
    const store = useUserStore()
    mockLoginApi.mockResolvedValue({ code: 401, message: '错误' })

    const result = await store.login({ username: 'admin', password: 'wrong', role: 'admin' })
    expect(result).toBe(false)
  })

  it('logout clears state even if API fails', async () => {
    const store = useUserStore()
    store.setToken('token')
    store.setUser({ id: 1, username: 'admin', role: 'admin', name: 'Admin', created_at: '' })
    mockLogoutApi.mockRejectedValue(new Error('network error'))

    await store.logout()
    expect(store.token).toBeNull()
    expect(store.user).toBeNull()
    expect(store.isLogin).toBe(false)
  })

  it('hasRole with single role', () => {
    const store = useUserStore()
    store.setUser({ id: 1, username: 'admin', role: 'admin', name: 'Admin', created_at: '' })
    expect(store.hasRole('admin')).toBe(true)
    expect(store.hasRole('employee')).toBe(false)
  })

  it('hasRole with array of roles', () => {
    const store = useUserStore()
    store.setUser({ id: 1, username: 'sup', role: 'supervisor', name: '主管', created_at: '' })
    expect(store.hasRole(['admin', 'supervisor'])).toBe(true)
    expect(store.hasRole(['admin', 'employee'])).toBe(false)
  })

  it('hasRole returns false when not logged in', () => {
    const store = useUserStore()
    expect(store.hasRole('admin')).toBe(false)
    expect(store.hasRole(['admin', 'supervisor'])).toBe(false)
  })

  it('fetchCurrentUser updates user on success', async () => {
    const store = useUserStore()
    mockGetCurrentUserApi.mockResolvedValue({
      code: 200,
      data: { id: 2, username: 'emp', role: 'employee', name: '员工', created_at: '2024-06-01' },
    })

    const result = await store.fetchCurrentUser()
    expect(result).toBeTruthy()
    expect(store.user?.username).toBe('emp')
  })

  it('fetchCurrentUser clears state on failure', async () => {
    const store = useUserStore()
    store.setToken('expired-token')
    store.setUser({ id: 1, username: 'admin', role: 'admin', name: 'Admin', created_at: '' })
    mockGetCurrentUserApi.mockRejectedValue(new Error('401'))

    const result = await store.fetchCurrentUser()
    expect(result).toBeNull()
    expect(store.token).toBeNull()
    expect(store.user).toBeNull()
  })
})
