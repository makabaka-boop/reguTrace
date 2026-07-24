import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockGet, mockPost, mockDelete } = vi.hoisted(() => ({
  mockGet: vi.fn(),
  mockPost: vi.fn(),
  mockDelete: vi.fn(),
}))

vi.mock('@/api/request', () => ({
  default: {
    get: mockGet,
    post: mockPost,
    delete: mockDelete,
  },
}))

import { markAsRead, markAsUnread, getMyReadingStatus } from '@/api/reading'

describe('reading API', () => {
  beforeEach(() => vi.clearAllMocks())

  it('markAsRead posts to correct URL', async () => {
    mockPost.mockResolvedValue({ code: 200, message: 'ok' })
    await markAsRead(42)
    expect(mockPost).toHaveBeenCalledWith('/reading/42')
  })

  it('markAsUnread sends DELETE to correct URL', async () => {
    mockDelete.mockResolvedValue({ code: 200, message: 'ok' })
    await markAsUnread(42)
    expect(mockDelete).toHaveBeenCalledWith('/reading/42')
  })

  it('getMyReadingStatus passes pagination params', async () => {
    mockGet.mockResolvedValue({ code: 200, data: { items: [], total: 0, page: 1, page_size: 10 } })
    await getMyReadingStatus({ page: 2, page_size: 5 })
    expect(mockGet).toHaveBeenCalledWith('/reading/my-status', { params: { page: 2, page_size: 5 } })
  })

  it('getMyReadingStatus passes expiry filter', async () => {
    mockGet.mockResolvedValue({ code: 200, data: { items: [], total: 0, page: 1, page_size: 10 } })
    await getMyReadingStatus({ review_expiry_status: 'overdue' })
    expect(mockGet).toHaveBeenCalledWith('/reading/my-status', { params: { review_expiry_status: 'overdue' } })
  })
})
