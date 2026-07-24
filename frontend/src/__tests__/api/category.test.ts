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

import { getCategoryTree, getCategoryList, getCategoryDetail, createCategory, updateCategory, deleteCategory, moveCategory, mergeCategory, copyCategory, deactivateCategory } from '@/api/category'

describe('category API', () => {
  beforeEach(() => vi.clearAllMocks())

  it('getCategoryTree with include_inactive param', async () => {
    mockGet.mockResolvedValue({ code: 200, data: [] })
    await getCategoryTree(true)
    expect(mockGet).toHaveBeenCalledWith('/categories', { params: { include_inactive: true } })
  })

  it('getCategoryTree default include_inactive=false', async () => {
    mockGet.mockResolvedValue({ code: 200, data: [] })
    await getCategoryTree()
    expect(mockGet).toHaveBeenCalledWith('/categories', { params: { include_inactive: false } })
  })

  it('getCategoryList with group_id', async () => {
    mockGet.mockResolvedValue({ code: 200, data: [] })
    await getCategoryList(5)
    expect(mockGet).toHaveBeenCalledWith('/categories/list', { params: { group_id: 5 } })
  })

  it('getCategoryDetail builds correct URL', async () => {
    mockGet.mockResolvedValue({ code: 200, data: {} })
    await getCategoryDetail(42)
    expect(mockGet).toHaveBeenCalledWith('/categories/42')
  })

  it('createCategory posts data', async () => {
    const data = { name: '新目录', code: 'NEW', sort_order: 1 }
    mockPost.mockResolvedValue({ code: 200, data: {} })
    await createCategory(data)
    expect(mockPost).toHaveBeenCalledWith('/categories', data)
  })

  it('updateCategory puts data with id', async () => {
    const data = { name: '更新' }
    mockPut.mockResolvedValue({ code: 200, data: {} })
    await updateCategory(10, data)
    expect(mockPut).toHaveBeenCalledWith('/categories/10', data)
  })

  it('deleteCategory builds correct URL', async () => {
    mockDelete.mockResolvedValue({ code: 200 })
    await deleteCategory(7)
    expect(mockDelete).toHaveBeenCalledWith('/categories/7')
  })

  it('moveCategory sends target_parent_id', async () => {
    mockPost.mockResolvedValue({ code: 200, data: {} })
    await moveCategory(3, 5)
    expect(mockPost).toHaveBeenCalledWith('/categories/3/move', { target_parent_id: 5 })
  })

  it('mergeCategory sends target_category_id', async () => {
    mockPost.mockResolvedValue({ code: 200 })
    await mergeCategory(2, 8)
    expect(mockPost).toHaveBeenCalledWith('/categories/2/merge', { target_category_id: 8 })
  })

  it('copyCategory with optional target_parent_id', async () => {
    mockPost.mockResolvedValue({ code: 200 })
    await copyCategory(1, 3)
    expect(mockPost).toHaveBeenCalledWith('/categories/1/copy', { target_group_id: 3, target_parent_id: undefined })
  })

  it('copyCategory with target_parent_id', async () => {
    mockPost.mockResolvedValue({ code: 200 })
    await copyCategory(1, 3, 5)
    expect(mockPost).toHaveBeenCalledWith('/categories/1/copy', { target_group_id: 3, target_parent_id: 5 })
  })

  it('deactivateCategory posts to correct endpoint', async () => {
    mockPost.mockResolvedValue({ code: 200, data: {} })
    await deactivateCategory(9)
    expect(mockPost).toHaveBeenCalledWith('/categories/9/deactivate')
  })
})
