import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  getCategoryTree,
  createCategory,
  updateCategory,
  deleteCategory,
  moveCategory,
  mergeCategory,
  copyCategory,
  deactivateCategory,
  type CategoryNode,
  type CategoryCreate,
  type CategoryUpdate
} from '@/api/category'
import { message } from 'ant-design-vue'

export const useCategoryStore = defineStore('category', () => {
  const treeData = ref<CategoryNode[]>([])
  const selectedCategoryId = ref<number | null>(null)
  const loading = ref(false)

  const selectedCategory = computed(() => {
    return findNodeById(treeData.value, selectedCategoryId.value)
  })

  const findNodeById = (nodes: CategoryNode[], id: number | null): CategoryNode | null => {
    if (!id) return null
    for (const node of nodes) {
      if (node.id === id) return node
      if (node.children) {
        const found = findNodeById(node.children, id)
        if (found) return found
      }
    }
    return null
  }

  const getSelectOptions = (nodes: CategoryNode[], level = 0): { label: string; value: number; disabled?: boolean }[] => {
    let options: { label: string; value: number; disabled?: boolean }[] = []
    for (const node of nodes) {
      options.push({
        label: '　'.repeat(level) + (level > 0 ? '└ ' : '') + node.name,
        value: node.id,
        disabled: !node.is_active
      })
      if (node.children && node.children.length > 0) {
        options = options.concat(getSelectOptions(node.children, level + 1))
      }
    }
    return options
  }

  const categoryOptions = computed(() => getSelectOptions(treeData.value))

  const fetchTree = async (include_inactive = false) => {
    loading.value = true
    try {
      const res = await getCategoryTree(include_inactive)
      if (res.code === 200) {
        treeData.value = res.data || []
      }
    } finally {
      loading.value = false
    }
  }

  const create = async (data: CategoryCreate) => {
    const res = await createCategory(data)
    if (res.code === 200) {
      message.success('创建成功')
      fetchTree()
      return res.data
    }
    return null
  }

  const update = async (id: number, data: CategoryUpdate) => {
    const res = await updateCategory(id, data)
    if (res.code === 200) {
      message.success('更新成功')
      fetchTree()
      return res.data
    }
    return null
  }

  const remove = async (id: number) => {
    const res = await deleteCategory(id)
    if (res.code === 200) {
      message.success('删除成功')
      if (selectedCategoryId.value === id) {
        selectedCategoryId.value = null
      }
      fetchTree()
      return true
    }
    return false
  }

  const move = async (id: number, target_parent_id: number) => {
    const res = await moveCategory(id, target_parent_id)
    if (res.code === 200) {
      message.success('移动成功')
      fetchTree()
      return true
    }
    return false
  }

  const merge = async (id: number, target_category_id: number) => {
    const res = await mergeCategory(id, target_category_id)
    if (res.code === 200) {
      message.success('合并成功')
      if (selectedCategoryId.value === id) {
        selectedCategoryId.value = target_category_id
      }
      fetchTree()
      return true
    }
    return false
  }

  const copy = async (id: number, target_group_id: number, target_parent_id?: number) => {
    const res = await copyCategory(id, target_group_id, target_parent_id)
    if (res.code === 200) {
      message.success('复制成功')
      fetchTree()
      return true
    }
    return false
  }

  const deactivate = async (id: number) => {
    const res = await deactivateCategory(id)
    if (res.code === 200) {
      message.success('已停用')
      fetchTree()
      return true
    }
    return false
  }

  const setSelected = (id: number | null) => {
    selectedCategoryId.value = id
  }

  return {
    treeData,
    selectedCategoryId,
    selectedCategory,
    categoryOptions,
    loading,
    fetchTree,
    create,
    update,
    remove,
    move,
    merge,
    copy,
    deactivate,
    setSelected
  }
})
