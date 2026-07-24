import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

const mocks = vi.hoisted(() => ({
  mockGetTree: vi.fn(),
  mockCreate: vi.fn(),
  mockUpdate: vi.fn(),
  mockDelete: vi.fn(),
  mockMove: vi.fn(),
  mockMerge: vi.fn(),
  mockCopy: vi.fn(),
  mockDeactivate: vi.fn(),
}))

vi.mock('@/api/category', () => ({
  getCategoryTree: (...args: any[]) => mocks.mockGetTree(...args),
  createCategory: (...args: any[]) => mocks.mockCreate(...args),
  updateCategory: (...args: any[]) => mocks.mockUpdate(...args),
  deleteCategory: (...args: any[]) => mocks.mockDelete(...args),
  moveCategory: (...args: any[]) => mocks.mockMove(...args),
  mergeCategory: (...args: any[]) => mocks.mockMerge(...args),
  copyCategory: (...args: any[]) => mocks.mockCopy(...args),
  deactivateCategory: (...args: any[]) => mocks.mockDeactivate(...args),
}))

vi.mock('ant-design-vue', () => ({
  message: {
    success: vi.fn(),
    error: vi.fn(),
  },
}))

import { useCategoryStore } from '@/stores/category'
import type { CategoryNode } from '@/api/category'

const mockTreeData: CategoryNode[] = [
  {
    id: 1, name: '行政制度', code: 'ADMIN', sort_order: 1, is_active: true, level: 1, path: '1',
    created_at: '', updated_at: '',
    children: [
      {
        id: 2, name: '考勤制度', code: 'ATTEND', parent_id: 1, sort_order: 1, is_active: true, level: 2, path: '1/2',
        created_at: '', updated_at: '',
        children: []
      },
      {
        id: 3, name: '请假制度', code: 'LEAVE', parent_id: 1, sort_order: 2, is_active: false, level: 2, path: '1/3',
        created_at: '', updated_at: '',
        children: []
      }
    ]
  },
  {
    id: 4, name: '财务制度', code: 'FIN', sort_order: 2, is_active: true, level: 1, path: '4',
    created_at: '', updated_at: '',
    children: []
  }
]

describe('category store', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    setActivePinia(createPinia())
  })

  it('initial state', () => {
    const store = useCategoryStore()
    expect(store.treeData).toEqual([])
    expect(store.selectedCategoryId).toBeNull()
    expect(store.loading).toBe(false)
    expect(store.selectedCategory).toBeNull()
  })

  it('fetchTree loads tree data', async () => {
    const store = useCategoryStore()
    mocks.mockGetTree.mockResolvedValue({ code: 200, data: mockTreeData })

    await store.fetchTree()
    expect(store.treeData).toHaveLength(2)
    expect(store.treeData[0].name).toBe('行政制度')
    expect(store.loading).toBe(false)
  })

  it('fetchTree sets loading correctly', async () => {
    const store = useCategoryStore()
    let resolveApi: (v: any) => void
    mocks.mockGetTree.mockReturnValue(new Promise(res => { resolveApi = res }))

    const promise = store.fetchTree()
    expect(store.loading).toBe(true)

    resolveApi!({ code: 200, data: [] })
    await promise
    expect(store.loading).toBe(false)
  })

  it('setSelected updates selectedCategoryId', () => {
    const store = useCategoryStore()
    store.treeData = mockTreeData
    store.setSelected(2)
    expect(store.selectedCategoryId).toBe(2)
    expect(store.selectedCategory?.name).toBe('考勤制度')
  })

  it('selectedCategory finds node in tree', () => {
    const store = useCategoryStore()
    store.treeData = mockTreeData
    store.setSelected(1)
    expect(store.selectedCategory?.name).toBe('行政制度')

    store.setSelected(4)
    expect(store.selectedCategory?.name).toBe('财务制度')
  })

  it('selectedCategory returns null for unknown id', () => {
    const store = useCategoryStore()
    store.treeData = mockTreeData
    store.setSelected(999)
    expect(store.selectedCategory).toBeNull()
  })

  it('categoryOptions builds flat select options', () => {
    const store = useCategoryStore()
    store.treeData = mockTreeData
    const options = store.categoryOptions
    expect(options.length).toBe(4)
    expect(options[0].label).toContain('行政制度')
    expect(options[1].label).toContain('考勤制度')
    expect(options[2].label).toContain('请假制度')
    expect(options[3].label).toContain('财务制度')
  })

  it('categoryOptions marks inactive as disabled', () => {
    const store = useCategoryStore()
    store.treeData = mockTreeData
    const options = store.categoryOptions
    const leaveOption = options.find(o => o.value === 3)
    expect(leaveOption?.disabled).toBe(true)
    const attendOption = options.find(o => o.value === 2)
    expect(attendOption?.disabled).toBe(false)
  })

  it('create success refreshes tree', async () => {
    const store = useCategoryStore()
    mocks.mockCreate.mockResolvedValue({ code: 200, data: { id: 5 } })
    mocks.mockGetTree.mockResolvedValue({ code: 200, data: mockTreeData })

    const result = await store.create({ name: '新目录' })
    expect(result).toBeTruthy()
    expect(mocks.mockGetTree).toHaveBeenCalled()
  })

  it('create failure returns null', async () => {
    const store = useCategoryStore()
    mocks.mockCreate.mockResolvedValue({ code: 400, message: '失败' })
    const result = await store.create({ name: '新目录' })
    expect(result).toBeNull()
  })

  it('update success refreshes tree', async () => {
    const store = useCategoryStore()
    mocks.mockUpdate.mockResolvedValue({ code: 200, data: { id: 1, name: '更新' } })
    mocks.mockGetTree.mockResolvedValue({ code: 200, data: [] })

    const result = await store.update(1, { name: '更新' })
    expect(result).toBeTruthy()
    expect(mocks.mockGetTree).toHaveBeenCalled()
  })

  it('remove success clears selection and refreshes', async () => {
    const store = useCategoryStore()
    store.treeData = mockTreeData
    store.setSelected(2)
    mocks.mockDelete.mockResolvedValue({ code: 200 })
    mocks.mockGetTree.mockResolvedValue({ code: 200, data: [] })

    const result = await store.remove(2)
    expect(result).toBe(true)
    expect(store.selectedCategoryId).toBeNull()
    expect(mocks.mockGetTree).toHaveBeenCalled()
  })

  it('remove does not clear selection for different id', async () => {
    const store = useCategoryStore()
    store.treeData = mockTreeData
    store.setSelected(1)
    mocks.mockDelete.mockResolvedValue({ code: 200 })
    mocks.mockGetTree.mockResolvedValue({ code: 200, data: [] })

    await store.remove(2)
    expect(store.selectedCategoryId).toBe(1)
  })

  it('merge updates selected id to target', async () => {
    const store = useCategoryStore()
    store.treeData = mockTreeData
    store.setSelected(2)
    mocks.mockMerge.mockResolvedValue({ code: 200 })
    mocks.mockGetTree.mockResolvedValue({ code: 200, data: [] })

    await store.merge(2, 4)
    expect(store.selectedCategoryId).toBe(4)
  })

  it('deactivate refreshes tree on success', async () => {
    const store = useCategoryStore()
    mocks.mockDeactivate.mockResolvedValue({ code: 200, data: {} })
    mocks.mockGetTree.mockResolvedValue({ code: 200, data: [] })

    const result = await store.deactivate(3)
    expect(result).toBe(true)
    expect(mocks.mockGetTree).toHaveBeenCalled()
  })

  it('move refreshes tree on success', async () => {
    const store = useCategoryStore()
    mocks.mockMove.mockResolvedValue({ code: 200, data: {} })
    mocks.mockGetTree.mockResolvedValue({ code: 200, data: [] })

    const result = await store.move(2, 4)
    expect(result).toBe(true)
  })

  it('copy refreshes tree on success', async () => {
    const store = useCategoryStore()
    mocks.mockCopy.mockResolvedValue({ code: 200 })
    mocks.mockGetTree.mockResolvedValue({ code: 200, data: [] })

    const result = await store.copy(1, 1)
    expect(result).toBe(true)
  })
})
