import { describe, it, expect } from 'vitest'
import { login, logout, getCurrentUser } from '@/api/auth'
import { mockRequest } from '@/test/setup'

describe('auth api', () => {
  it('login posts username/password/role to /auth/login', async () => {
    const payload = { id: 1, username: 'alice', role: 'employee', name: 'Alice', created_at: 't', token: 'tok' }
    mockRequest.post.mockResolvedValue({ code: 200, data: payload })

    const res = await login({ username: 'alice', password: 'pw', role: 'employee' })

    expect(mockRequest.post).toHaveBeenCalledWith(
      expect.any(String),
      { username: 'alice', password: 'pw', role: 'employee' }
    )
    const [url] = mockRequest.post.mock.calls[0]
    expect(url).toBe('/auth/login')
    expect(res.data.token).toBe('tok')
  })

  it('logout posts to /auth/logout', async () => {
    mockRequest.post.mockResolvedValue({ code: 200, data: null })
    await logout()
    expect(mockRequest.post).toHaveBeenCalledTimes(1)
    expect(mockRequest.post.mock.calls[0][0]).toBe('/auth/logout')
  })

  it('getCurrentUser gets /auth/me', async () => {
    mockRequest.get.mockResolvedValue({
      code: 200,
      data: { id: 1, username: 'bob', role: 'admin', name: 'Bob', created_at: 't' },
    })
    const res = await getCurrentUser()
    expect(mockRequest.get).toHaveBeenCalledWith('/auth/me')
    expect(res.data.username).toBe('bob')
  })
})
