import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockGet, mockPost, mockPut, mockDelete } = vi.hoisted(() => ({
  mockGet: vi.fn(),
  mockPost: vi.fn(),
  mockPut: vi.fn(),
  mockDelete: vi.fn(),
}))

vi.mock('@/api/request', () => ({
  default: {
    get: mockGet,
    post: mockPost,
    put: mockPut,
    delete: mockDelete,
  },
}))

import { getKnowledgeList, getMyKnowledge, getKnowledgeDetail, createKnowledge, updateKnowledge, deleteKnowledge } from '@/api/knowledge'

describe('knowledge API', () => {
  beforeEach(() => vi.clearAllMocks())

  it('getKnowledgeList assembles params correctly', async () => {
    mockGet.mockResolvedValue({ code: 200, data: { items: [], total: 0, page: 1, page_size: 10 } })
    const params = { category_id: 5, page: 2, page_size: 20, review_status: 'approved' as const }
    await getKnowledgeList(params)
    expect(mockGet).toHaveBeenCalledWith('/knowledge', { params })
  })

  it('getKnowledgeList passes keyword', async () => {
    mockGet.mockResolvedValue({ code: 200, data: { items: [], total: 0, page: 1, page_size: 10 } })
    await getKnowledgeList({ keyword: '测试' })
    expect(mockGet).toHaveBeenCalledWith('/knowledge', { params: { keyword: '测试' } })
  })

  it('getMyKnowledge calls correct endpoint', async () => {
    mockGet.mockResolvedValue({ code: 200, data: { items: [], total: 0, page: 1, page_size: 10 } })
    await getMyKnowledge({ page: 1, page_size: 10 })
    expect(mockGet).toHaveBeenCalledWith('/knowledge/my', { params: { page: 1, page_size: 10 } })
  })

  it('getKnowledgeDetail builds URL with id', async () => {
    mockGet.mockResolvedValue({ code: 200, data: {} })
    await getKnowledgeDetail(100)
    expect(mockGet).toHaveBeenCalledWith('/knowledge/100')
  })

  it('createKnowledge posts to /knowledge', async () => {
    const data = { title: '新制度', content: '<p>内容</p>', category_id: 1 }
    mockPost.mockResolvedValue({ code: 200, data: {} })
    await createKnowledge(data)
    expect(mockPost).toHaveBeenCalledWith('/knowledge', data)
  })

  it('updateKnowledge puts data', async () => {
    const data = { title: '更新标题' }
    mockPut.mockResolvedValue({ code: 200, data: {} })
    await updateKnowledge(55, data)
    expect(mockPut).toHaveBeenCalledWith('/knowledge/55', data)
  })

  it('deleteKnowledge sends DELETE with id', async () => {
    mockDelete.mockResolvedValue({ code: 200 })
    await deleteKnowledge(33)
    expect(mockDelete).toHaveBeenCalledWith('/knowledge/33')
  })
})
