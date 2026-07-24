import { describe, it, expect } from 'vitest'
import {
  getPendingList,
  getStatistics,
  approveKnowledge,
  rejectKnowledge,
  batchApprove,
  batchReject,
} from '@/api/review'
import { mockRequest } from '@/test/setup'

describe('review api', () => {
  it('getPendingList passes pagination params', async () => {
    mockRequest.get.mockResolvedValue({ code: 200, data: { items: [], total: 0 } })
    await getPendingList({ page: 1, page_size: 20 })
    expect(mockRequest.get).toHaveBeenCalledWith('/review/pending', { params: { page: 1, page_size: 20 } })
  })

  it('getStatistics calls statistics endpoint', async () => {
    mockRequest.get.mockResolvedValue({
      code: 200,
      data: { pending_count: 1, approved_count: 2, rejected_count: 3 },
    })
    const res = await getStatistics()
    expect(mockRequest.get).toHaveBeenCalledWith('/review/statistics')
    expect(res.data.pending_count).toBe(1)
  })

  it('approveKnowledge posts optional remark and new_category_id', async () => {
    mockRequest.post.mockResolvedValue({ code: 200, data: {} })
    await approveKnowledge(7, { remark: 'ok', new_category_id: 3 })
    expect(mockRequest.post).toHaveBeenCalledWith('/review/7/approve', { remark: 'ok', new_category_id: 3 })
  })

  it('approveKnowledge defaults to empty body', async () => {
    mockRequest.post.mockResolvedValue({ code: 200, data: {} })
    await approveKnowledge(7)
    expect(mockRequest.post).toHaveBeenCalledWith('/review/7/approve', {})
  })

  it('rejectKnowledge posts remark', async () => {
    mockRequest.post.mockResolvedValue({ code: 200, data: {} })
    await rejectKnowledge(8, { remark: 'bad' })
    expect(mockRequest.post).toHaveBeenCalledWith('/review/8/reject', { remark: 'bad' })
  })

  it('batchApprove posts id list', async () => {
    mockRequest.post.mockResolvedValue({ code: 200 })
    await batchApprove({ knowledge_ids: [1, 2, 3], remark: 'go' })
    expect(mockRequest.post).toHaveBeenCalledWith('/review/batch-approve', { knowledge_ids: [1, 2, 3], remark: 'go' })
  })

  it('batchReject posts id list', async () => {
    mockRequest.post.mockResolvedValue({ code: 200 })
    await batchReject({ knowledge_ids: [4], remark: 'no' })
    expect(mockRequest.post).toHaveBeenCalledWith('/review/batch-reject', { knowledge_ids: [4], remark: 'no' })
  })
})
