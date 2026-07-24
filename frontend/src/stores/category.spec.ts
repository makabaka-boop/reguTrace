import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useCategoryStore } from '@/stores/category'
import { mockRequest, mockMessage } from '@/test/setup'
import type { CategoryNode } from '@/api/category'

function buildNode(overrides: Partial<CategoryNode> = {}): CategoryNode {
  return {
    id: 1,
    name: '根',
    code: 'R',
    parent_id: null,
    group_id: null,
    sort_order: 0,
    is_active: true,
    level: 1,
    path: '1',
    created_at: 't',
    updated_at: 't',
    children: [],
    ...overrides,
  }
}

describe('category store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('fetchTree loads tree and clears loading', async () => {
    const store = useCategoryStore()
    const tree = [buildNode({ id: 1 }), buildNode({ id: 2, name: 'B' })]
    mockRequest.get.mockResolvedValue({ code: 200, data: tree })

    await store.fetchTree()
    expect(store.treeData).toHaveLength(2)
    expect(store.loading).toBe(false)
    expect(mockRequest.get).toHaveBeenCalledWith('/categories', { params: { include_inactive: false } })
  })

  it('fetchTree respects include_inactive flag', async () => {
    const store = useCategoryStore()
    mockRequest.get.mockResolvedValue({ code: 200, data: [] })
    await store.fetchTree(true)
    expect(mockRequest.get).toHaveBeenCalledWith('/categories', { params: { include_inactive: true } })
  })

  it('setSelected updates selectedCategoryId', () => {
    const store = useCategoryStore()
    store.treeData = [buildNode({ id: 5, name: '选我' })]
    store.setSelected(5)
    expect(store.selectedCategoryId).toBe(5)
    expect(store.selectedCategory?.name).toBe('选我')
  })

  it('selectedCategory returns null for unknown id', () => {
    const store = useCategoryStore()
    store.treeData = [buildNode({ id: 1 })]
    store.setSelected(999)
    expect(store.selectedCategory).toBeNull()
  })

  it('findNodeById searches nested children', () => {
    const store = useCategoryStore()
    const child = buildNode({ id: 2, name: '子', parent_id: 1 })
    const grand = buildNode({ id: 3, name: '孙', parent_id: 2 })
    child.children = [grand]
    store.treeData = [buildNode({ id: 1, children: [child] })]

    store.setSelected(3)
    expect(store.selectedCategory?.name).toBe('孙')
  })

  it('categoryOptions builds indented labels and disables inactive nodes', () => {
    const store = useCategoryStore()
    const child = buildNode({ id: 2, name: '子', parent_id: 1, is_active: false })
    store.treeData = [buildNode({ id: 1, children: [child] })]

    const options = store.categoryOptions
    expect(options).toHaveLength(2)
    expect(options[0].label).toContain('根')
    expect(options[0].disabled).toBe(false)
    expect(options[1].label).toContain('子')
    expect(options[1].disabled).toBe(true)
  })

  it('create success shows message and refreshes tree', async () => {
    const store = useCategoryStore()
    mockRequest.get.mockResolvedValue({ code: 200, data: [] })
    mockRequest.post.mockResolvedValue({ code: 200, data: buildNode({ id: 9 }) })

    await store.create({ name: '新分类' })
    expect(mockMessage.success).toHaveBeenCalled()
    expect(mockRequest.get).toHaveBeenCalled()
  })

  it('create with non-200 returns null', async () => {
    const store = useCategoryStore()
    mockRequest.post.mockResolvedValue({ code: 400, message: 'fail' })
    const res = await store.create({ name: 'x' })
    expect(res).toBeNull()
  })

  it('update success refreshes tree', async () => {
    const store = useCategoryStore()
    mockRequest.get.mockResolvedValue({ code: 200, data: [] })
    mockRequest.put.mockResolvedValue({ code: 200, data: {} })
    await store.update(1, { name: '改名' })
    expect(mockRequest.put).toHaveBeenCalledWith('/categories/1', { name: '改名' })
    expect(mockMessage.success).toHaveBeenCalled()
  })

  it('remove clears selection if deleting selected node', async () => {
    const store = useCategoryStore()
    mockRequest.get.mockResolvedValue({ code: 200, data: [] })
    mockRequest.delete.mockResolvedValue({ code: 200 })
    store.treeData = [buildNode({ id: 7 })]
    store.setSelected(7)

    const ok = await store.remove(7)
    expect(ok).toBe(true)
    expect(store.selectedCategoryId).toBeNull()
  })

  it('remove returns false on failure', async () => {
    const store = useCategoryStore()
    mockRequest.delete.mockResolvedValue({ code: 400, message: 'nope' })
    const ok = await store.remove(1)
    expect(ok).toBe(false)
  })

  it('move and merge update selection appropriately', async () => {
    const store = useCategoryStore()
    mockRequest.get.mockResolvedValue({ code: 200, data: [] })
    mockRequest.post
      .mockResolvedValueOnce({ code: 200, data: {} })
      .mockResolvedValueOnce({ code: 200 })

    await store.move(1, 2)
    expect(mockMessage.success).toHaveBeenCalled()

    store.setSelected(3)
    await store.merge(3, 5)
    expect(store.selectedCategoryId).toBe(5)
  })

  it('copy and deactivate return true on success', async () => {
    const store = useCategoryStore()
    mockRequest.get.mockResolvedValue({ code: 200, data: [] })
    mockRequest.post
      .mockResolvedValueOnce({ code: 200 })
      .mockResolvedValueOnce({ code: 200, data: {} })

    expect(await store.copy(1, 2)).toBe(true)
    expect(await store.deactivate(1)).toBe(true)
  })
})
