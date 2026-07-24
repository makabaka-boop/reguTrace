import { describe, it, expect } from 'vitest'
import { markAsRead, markAsUnread, getMyReadingStatus } from '@/api/reading'
import { mockRequest } from '@/test/setup'

describe('reading api', () => {
  it('markAsRead posts to /reading/:id', async () => {
    mockRequest.post.mockResolvedValue({ code: 200, data: null })
    await markAsRead(15)
    expect(mockRequest.post).toHaveBeenCalledWith('/reading/15')
  })

  it('markAsUnread deletes /reading/:id', async () => {
    mockRequest.delete.mockResolvedValue({ code: 200, data: null })
    await markAsUnread(15)
    expect(mockRequest.delete).toHaveBeenCalledWith('/reading/15')
  })

  it('getMyReadingStatus passes pagination and expiry filter', async () => {
    mockRequest.get.mockResolvedValue({
      code: 200,
      data: { items: [], total: 0, page: 1, page_size: 10 },
    })
    await getMyReadingStatus({ page: 2, page_size: 5, review_expiry_status: 'overdue' } as any)
    expect(mockRequest.get).toHaveBeenCalledWith('/reading/my-status', {
      params: { page: 2, page_size: 5, review_expiry_status: 'overdue' },
    })
  })
})
