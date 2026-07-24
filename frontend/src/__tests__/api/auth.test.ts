import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockGet, mockPost } = vi.hoisted(() => ({
  mockGet: vi.fn(),
  mockPost: vi.fn(),
}))

vi.mock('@/api/request', () => ({
  default: {
    get: mockGet,
    post: mockPost,
  },
}))

import { login, logout, getCurrentUser } from '@/api/auth'

describe('auth API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('login sends correct params', async () => {
    mockGet.mockResolvedValue({ code: 200, data: {} })
    mockPost.mockResolvedValue({ code: 200, data: { id: 1, username: 'admin', role: 'admin', name: 'Admin', token: 'abc', created_at: '2024-01-01' } })

    const params = { username: 'admin', password: '123', role: 'admin' }
    await login(params)

    expect(mockPost).toHaveBeenCalledWith('/auth/login', params)
  })

  it('logout posts to correct endpoint', async () => {
    mockPost.mockResolvedValue({ code: 200, message: 'ok' })
    await logout()
    expect(mockPost).toHaveBeenCalledWith('/auth/logout')
  })

  it('getCurrentUser calls correct endpoint', async () => {
    mockGet.mockResolvedValue({ code: 200, data: { id: 1, username: 'admin', role: 'admin', name: 'Admin', created_at: '2024-01-01' } })
    await getCurrentUser()
    expect(mockGet).toHaveBeenCalledWith('/auth/me')
  })
})
