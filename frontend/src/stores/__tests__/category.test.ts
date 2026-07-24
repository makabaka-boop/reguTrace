/**
 * 分类 store 测试：树数据加载、选中态、下拉选项组装、增删改与状态更新。
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

const getCategoryTree = vi.fn()
const createCategory = vi.fn()
const updateCategory = vi.fn()
const deleteCategory = vi.fn()
const moveCategory = vi.fn()
const mergeCategory = vi.fn()
const copyCategory = vi.fn()
const deactivateCategory = vi.fn()

vi.mock('@/api/category', () => ({
  getCategoryTree: (...a: any[]) => getCategoryTree(...a),
  createCategory: (...a: any[]) => createCategory(...a),
  updateCategory: (...a: any[]) => updateCategory(...a),
  deleteCategory: (...a: any[]) => deleteCategory(...a),
  moveCategory: (...a: any[]) => moveCategory(...a),
  mergeCategory: (...a: any[]) => mergeCategory(...a),
  copyCategory: (...a: any[]) => copyCategory(...a),
  deactivateCategory: (...a: any[]) => deactivateCategory(...a),
}))

import { useCategoryStore } from '@/stores/category'

const sampleTree = [
  {
    id: 1, name: '人事制度', sort_order: 1, is_active: true, level: 1, path: '1',
    created_at: '', updated_at: '',
    children: [
      { id: 2, name: '考勤管理', sort_order: 1, is_active: true, level: 2, path: '1/2', created_at: '', updated_at: '', children: [] },
      { id: 3, name: '已停用', sort_order: 2, is_active: false, level: 2, path: '1/3', created_at: '', updated_at: '', children: [] },
    ],
  },
]

beforeEach(() => {
  setActivePinia(createPinia())
  vi.clearAllMocks()
})

describe('useCategoryStore - fetchTree', () => {
  it('成功时写入 treeData', async () => {
    getCategoryTree.mockResolvedValue({ code: 200, data: sampleTree })
    const store = useCategoryStore()
    await store.fetchTree()
    expect(store.treeData).toHaveLength(1)
    expect(store.loading).toBe(false)
  })

  it('非 200 时保持空树', async () => {
    getCategoryTree.mockResolvedValue({ code: 500, data: null })
    const store = useCategoryStore()
    await store.fetchTree()
    expect(store.treeData).toEqual([])
  })
})

describe('useCategoryStore - 选中态与查找', () => {
  it('setSelected 后 selectedCategory 递归查找命中子节点', async () => {
    getCategoryTree.mockResolvedValue({ code: 200, data: sampleTree })
    const store = useCategoryStore()
    await store.fetchTree()
    store.setSelected(2)
    expect(store.selectedCategoryId).toBe(2)
    expect(store.selectedCategory?.name).toBe('考勤管理')
  })

  it('selectedCategory 在 id 为 null 时为 null', () => {
    const store = useCategoryStore()
    store.setSelected(null)
    expect(store.selectedCategory).toBeNull()
  })
})

describe('useCategoryStore - categoryOptions', () => {
  it('按层级缩进生成下拉选项，并对停用项禁用', async () => {
    getCategoryTree.mockResolvedValue({ code: 200, data: sampleTree })
    const store = useCategoryStore()
    await store.fetchTree()
    const opts = store.categoryOptions
    expect(opts).toHaveLength(3)
    expect(opts[0].value).toBe(1)
    // 停用节点被标记 disabled
    const disabledOpt = opts.find(o => o.value === 3)
    expect(disabledOpt?.disabled).toBe(true)
    // 子节点带有缩进前缀
    expect(opts[1].label).toContain('└')
  })
})

describe('useCategoryStore - CRUD 与状态更新', () => {
  it('create 成功后返回数据并刷新树', async () => {
    createCategory.mockResolvedValue({ code: 200, data: { id: 10, name: '新' } })
    getCategoryTree.mockResolvedValue({ code: 200, data: sampleTree })
    const store = useCategoryStore()
    const res = await store.create({ name: '新' })
    expect(res).toEqual({ id: 10, name: '新' })
    expect(getCategoryTree).toHaveBeenCalled()
  })

  it('create 非 200 返回 null', async () => {
    createCategory.mockResolvedValue({ code: 400, data: null })
    const store = useCategoryStore()
    const res = await store.create({ name: '新' })
    expect(res).toBeNull()
  })

  it('remove 删除当前选中项后清空 selectedCategoryId', async () => {
    deleteCategory.mockResolvedValue({ code: 200 })
    getCategoryTree.mockResolvedValue({ code: 200, data: sampleTree })
    const store = useCategoryStore()
    store.setSelected(5)
    const ok = await store.remove(5)
    expect(ok).toBe(true)
    expect(store.selectedCategoryId).toBeNull()
  })

  it('merge 成功后把选中项切换到目标节点', async () => {
    mergeCategory.mockResolvedValue({ code: 200 })
    getCategoryTree.mockResolvedValue({ code: 200, data: sampleTree })
    const store = useCategoryStore()
    store.setSelected(2)
    const ok = await store.merge(2, 9)
    expect(ok).toBe(true)
    expect(store.selectedCategoryId).toBe(9)
  })

  it('move 失败时返回 false', async () => {
    moveCategory.mockResolvedValue({ code: 400 })
    const store = useCategoryStore()
    const ok = await store.move(1, 2)
    expect(ok).toBe(false)
  })

  it('deactivate 成功后返回 true 并刷新', async () => {
    deactivateCategory.mockResolvedValue({ code: 200 })
    getCategoryTree.mockResolvedValue({ code: 200, data: sampleTree })
    const store = useCategoryStore()
    const ok = await store.deactivate(2)
    expect(ok).toBe(true)
    expect(getCategoryTree).toHaveBeenCalled()
  })
})
