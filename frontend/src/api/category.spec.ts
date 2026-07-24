import { describe, it, expect } from 'vitest'
import {
  getCategoryTree,
  getCategoryList,
  getCategoryDetail,
  createCategory,
  updateCategory,
  deleteCategory,
  moveCategory,
  mergeCategory,
  copyCategory,
  deactivateCategory,
} from '@/api/category'
import { mockRequest } from '@/test/setup'

describe('category api', () => {
  it('getCategoryTree passes include_inactive flag', async () => {
    mockRequest.get.mockResolvedValue({ code: 200, data: [] })
    await getCategoryTree(true)
    expect(mockRequest.get).toHaveBeenCalledWith('/categories', { params: { include_inactive: true } })
  })

  it('getCategoryTree defaults include_inactive false', async () => {
    mockRequest.get.mockResolvedValue({ code: 200, data: [] })
    await getCategoryTree()
    expect(mockRequest.get).toHaveBeenCalledWith('/categories', { params: { include_inactive: false } })
  })

  it('getCategoryList passes optional group_id', async () => {
    mockRequest.get.mockResolvedValue({ code: 200, data: [] })
    await getCategoryList(3)
    expect(mockRequest.get).toHaveBeenCalledWith('/categories/list', { params: { group_id: 3 } })
  })

  it('getCategoryDetail builds url', async () => {
    mockRequest.get.mockResolvedValue({ code: 200, data: {} })
    await getCategoryDetail(5)
    expect(mockRequest.get).toHaveBeenCalledWith('/categories/5')
  })

  it('createCategory posts payload', async () => {
    mockRequest.post.mockResolvedValue({ code: 200, data: {} })
    await createCategory({ name: 'n', parent_id: 1, sort_order: 0 })
    expect(mockRequest.post).toHaveBeenCalledWith('/categories', { name: 'n', parent_id: 1, sort_order: 0 })
  })

  it('updateCategory puts payload', async () => {
    mockRequest.put.mockResolvedValue({ code: 200, data: {} })
    await updateCategory(2, { name: 'x', is_active: false })
    expect(mockRequest.put).toHaveBeenCalledWith('/categories/2', { name: 'x', is_active: false })
  })

  it('deleteCategory calls delete', async () => {
    mockRequest.delete.mockResolvedValue({ code: 200 })
    await deleteCategory(4)
    expect(mockRequest.delete).toHaveBeenCalledWith('/categories/4')
  })

  it('moveCategory posts target_parent_id', async () => {
    mockRequest.post.mockResolvedValue({ code: 200, data: {} })
    await moveCategory(3, 7)
    expect(mockRequest.post).toHaveBeenCalledWith('/categories/3/move', { target_parent_id: 7 })
  })

  it('mergeCategory posts target_category_id', async () => {
    mockRequest.post.mockResolvedValue({ code: 200 })
    await mergeCategory(3, 8)
    expect(mockRequest.post).toHaveBeenCalledWith('/categories/3/merge', { target_category_id: 8 })
  })

  it('copyCategory posts group and optional parent', async () => {
    mockRequest.post.mockResolvedValue({ code: 200 })
    await copyCategory(1, 2, 3)
    expect(mockRequest.post).toHaveBeenCalledWith('/categories/1/copy', { target_group_id: 2, target_parent_id: 3 })
  })

  it('copyCategory allows undefined parent', async () => {
    mockRequest.post.mockResolvedValue({ code: 200 })
    await copyCategory(1, 2)
    expect(mockRequest.post).toHaveBeenCalledWith('/categories/1/copy', { target_group_id: 2, target_parent_id: undefined })
  })

  it('deactivateCategory posts to deactivate endpoint', async () => {
    mockRequest.post.mockResolvedValue({ code: 200, data: {} })
    await deactivateCategory(6)
    expect(mockRequest.post).toHaveBeenCalledWith('/categories/6/deactivate')
  })
})
