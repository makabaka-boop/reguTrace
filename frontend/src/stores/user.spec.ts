import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useUserStore } from '@/stores/user'
import { mockRequest, mockMessage, mockRouter } from '@/test/setup'

describe('user store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
  })

  function buildUser(overrides: Record<string, any> = {}) {
    return {
      id: 1,
      username: 'alice',
      role: 'employee',
      name: 'Alice',
      created_at: '2025-01-01',
      token: 'abc',
      ...overrides,
    }
  }

  it('initial state is unauthenticated', () => {
    const store = useUserStore()
    expect(store.user).toBeNull()
    expect(store.token).toBeNull()
    expect(store.isLogin).toBe(false)
    expect(store.userRole).toBeNull()
    expect(store.userName).toBe('')
  })

  it('setToken persists to localStorage', () => {
    const store = useUserStore()
    store.setToken('t1')
    expect(store.token).toBe('t1')
    expect(localStorage.getItem('token')).toBe('t1')

    store.setToken(null)
    expect(store.token).toBeNull()
    expect(localStorage.getItem('token')).toBeNull()
  })

  it('setUser persists and serializes user', () => {
    const store = useUserStore()
    const u = { id: 2, username: 'b', role: 'admin' as const, name: 'B', created_at: 't' }
    store.setUser(u)
    expect(store.user).toEqual(u)
    expect(JSON.parse(localStorage.getItem('user')!)).toEqual(u)
  })

  it('loadUserFromStorage restores user', () => {
    const u = { id: 3, username: 'c', role: 'supervisor', name: 'C', created_at: 't' }
    localStorage.setItem('user', JSON.stringify(u))
    const store = useUserStore()
    store.loadUserFromStorage()
    expect(store.user?.id).toBe(3)
    expect(store.user?.username).toBe('c')
  })

  it('login success stores token/user and returns true', async () => {
    const store = useUserStore()
    mockRequest.post.mockResolvedValue({ code: 200, message: 'ok', data: buildUser() })

    const ok = await store.login({ username: 'alice', password: 'pw', role: 'employee' })
    expect(ok).toBe(true)
    expect(store.token).toBe('abc')
    expect(store.user?.name).toBe('Alice')
    expect(mockMessage.success).toHaveBeenCalled()
  })

  it('login failure returns false', async () => {
    const store = useUserStore()
    mockRequest.post.mockRejectedValue(new Error('bad'))
    const ok = await store.login({ username: 'x', password: 'y', role: 'employee' })
    expect(ok).toBe(false)
    expect(store.user).toBeNull()
  })

  it('login with non-200 returns false', async () => {
    const store = useUserStore()
    mockRequest.post.mockResolvedValue({ code: 401, message: 'fail', data: null })
    const ok = await store.login({ username: 'x', password: 'y', role: 'employee' })
    expect(ok).toBe(false)
  })

  it('logout clears state and navigates to login', async () => {
    const store = useUserStore()
    store.setToken('t')
    store.setUser({ id: 1, username: 'a', role: 'employee', name: 'A', created_at: 't' })
    mockRequest.post.mockResolvedValue({ code: 200, data: null })

    await store.logout()

    expect(store.token).toBeNull()
    expect(store.user).toBeNull()
    expect(localStorage.getItem('token')).toBeNull()
    expect(mockRouter.push).toHaveBeenCalledWith('/login')
    expect(mockMessage.info).toHaveBeenCalled()
  })

  it('logout clears state even if api fails', async () => {
    const store = useUserStore()
    store.setToken('t')
    store.setUser({ id: 1, username: 'a', role: 'employee', name: 'A', created_at: 't' })
    mockRequest.post.mockRejectedValue(new Error('network'))

    await store.logout()
    expect(store.token).toBeNull()
    expect(store.user).toBeNull()
  })

  it('fetchCurrentUser populates user on success', async () => {
    const store = useUserStore()
    store.setToken('t')
    mockRequest.get.mockResolvedValue({
      code: 200,
      data: { id: 9, username: 'me', role: 'supervisor', name: 'Me', created_at: 't' },
    })
    const res = await store.fetchCurrentUser()
    expect(res?.username).toBe('me')
    expect(store.user?.role).toBe('supervisor')
  })

  it('fetchCurrentUser clears state on failure', async () => {
    const store = useUserStore()
    store.setToken('t')
    store.setUser({ id: 1, username: 'old', role: 'employee', name: 'old', created_at: 't' })
    mockRequest.get.mockRejectedValue(new Error('401'))
    const res = await store.fetchCurrentUser()
    expect(res).toBeNull()
    expect(store.token).toBeNull()
    expect(store.user).toBeNull()
  })

  it('hasRole checks single and array roles', () => {
    const store = useUserStore()
    store.setUser({ id: 1, username: 'a', role: 'supervisor', name: 'A', created_at: 't' })
    expect(store.hasRole('supervisor')).toBe(true)
    expect(store.hasRole('admin')).toBe(false)
    expect(store.hasRole(['admin', 'supervisor'])).toBe(true)
    expect(store.hasRole(['admin', 'employee'])).toBe(false)
  })

  it('hasRole returns false when not logged in', () => {
    const store = useUserStore()
    expect(store.hasRole('admin')).toBe(false)
  })
})
