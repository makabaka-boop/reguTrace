import { describe, it, expect } from 'vitest'
import {
  getKnowledgeList,
  getMyKnowledge,
  getKnowledgeDetail,
  createKnowledge,
  updateKnowledge,
  deleteKnowledge,
} from '@/api/knowledge'
import { mockRequest } from '@/test/setup'

describe('knowledge api', () => {
  it('getKnowledgeList passes query params', async () => {
    mockRequest.get.mockResolvedValue({ code: 200, data: { items: [], total: 0, page: 1, page_size: 10 } })
    await getKnowledgeList({ category_id: 5, page: 2, page_size: 20, review_status: 'pending' })
    expect(mockRequest.get).toHaveBeenCalledWith('/knowledge', {
      params: { category_id: 5, page: 2, page_size: 20, review_status: 'pending' },
    })
  })

  it('getKnowledgeList omits undefined params', async () => {
    mockRequest.get.mockResolvedValue({ code: 200, data: { items: [], total: 0, page: 1, page_size: 10 } })
    await getKnowledgeList({})
    expect(mockRequest.get).toHaveBeenCalledWith('/knowledge', { params: {} })
  })

  it('getMyKnowledge calls /knowledge/my', async () => {
    mockRequest.get.mockResolvedValue({ code: 200, data: { items: [], total: 0, page: 1, page_size: 10 } })
    await getMyKnowledge({ page: 1, page_size: 5 })
    expect(mockRequest.get).toHaveBeenCalledWith('/knowledge/my', { params: { page: 1, page_size: 5 } })
  })

  it('getKnowledgeDetail builds detail url', async () => {
    mockRequest.get.mockResolvedValue({ code: 200, data: { id: 42 } })
    await getKnowledgeDetail(42)
    expect(mockRequest.get).toHaveBeenCalledWith('/knowledge/42')
  })

  it('createKnowledge posts payload', async () => {
    const payload = { title: 't', content: 'c', category_id: 1 }
    mockRequest.post.mockResolvedValue({ code: 200, data: { id: 1, ...payload } })
    await createKnowledge(payload)
    expect(mockRequest.post).toHaveBeenCalledWith('/knowledge', payload)
  })

  it('updateKnowledge puts payload to /knowledge/:id', async () => {
    mockRequest.put.mockResolvedValue({ code: 200, data: {} })
    await updateKnowledge(7, { title: 'new' })
    expect(mockRequest.put).toHaveBeenCalledWith('/knowledge/7', { title: 'new' })
  })

  it('deleteKnowledge calls delete on /knowledge/:id', async () => {
    mockRequest.delete.mockResolvedValue({ code: 200, data: null })
    await deleteKnowledge(9)
    expect(mockRequest.delete).toHaveBeenCalledWith('/knowledge/9')
  })
})
