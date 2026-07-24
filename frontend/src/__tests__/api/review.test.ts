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

import { getPendingList, getStatistics, approveKnowledge, rejectKnowledge, batchApprove, batchReject } from '@/api/review'

describe('review API', () => {
  beforeEach(() => vi.clearAllMocks())

  it('getPendingList passes pagination params', async () => {
    mockGet.mockResolvedValue({ code: 200, data: { items: [], total: 0, page: 1, page_size: 10 } })
    await getPendingList({ page: 1, page_size: 20 })
    expect(mockGet).toHaveBeenCalledWith('/review/pending', { params: { page: 1, page_size: 20 } })
  })

  it('getStatistics calls correct endpoint', async () => {
    mockGet.mockResolvedValue({ code: 200, data: { pending_count: 5, approved_count: 10, rejected_count: 2 } })
    await getStatistics()
    expect(mockGet).toHaveBeenCalledWith('/review/statistics')
  })

  it('approveKnowledge posts with correct URL', async () => {
    mockPost.mockResolvedValue({ code: 200, data: {} })
    await approveKnowledge(42, { remark: '通过' })
    expect(mockPost).toHaveBeenCalledWith('/review/42/approve', { remark: '通过' })
  })

  it('approveKnowledge works with empty data', async () => {
    mockPost.mockResolvedValue({ code: 200, data: {} })
    await approveKnowledge(42)
    expect(mockPost).toHaveBeenCalledWith('/review/42/approve', {})
  })

  it('rejectKnowledge posts with remark', async () => {
    mockPost.mockResolvedValue({ code: 200, data: {} })
    await rejectKnowledge(42, { remark: '内容不足' })
    expect(mockPost).toHaveBeenCalledWith('/review/42/reject', { remark: '内容不足' })
  })

  it('batchApprove posts ids', async () => {
    mockPost.mockResolvedValue({ code: 200 })
    await batchApprove({ knowledge_ids: [1, 2, 3], remark: '批量通过' })
    expect(mockPost).toHaveBeenCalledWith('/review/batch-approve', { knowledge_ids: [1, 2, 3], remark: '批量通过' })
  })

  it('batchReject posts ids', async () => {
    mockPost.mockResolvedValue({ code: 200 })
    await batchReject({ knowledge_ids: [4, 5], remark: '批量驳回' })
    expect(mockPost).toHaveBeenCalledWith('/review/batch-reject', { knowledge_ids: [4, 5], remark: '批量驳回' })
  })
})
