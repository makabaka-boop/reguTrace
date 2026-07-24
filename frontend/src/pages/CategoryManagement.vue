<template>
  <div class="category-management-page">
    <a-row :gutter="16">
      <a-col :xs="24" :lg="8">
        <a-card :bordered="false" class="tree-card" title="分类树">
          <CategoryTree
            ref="treeRef"
            @select="handleCategorySelect"
            @node-change="loadGroups"
          />
        </a-card>
      </a-col>
      <a-col :xs="24" :lg="16">
        <a-card :bordered="false" class="detail-card" title="详情">
          <template v-if="selectedCategory">
            <a-descriptions :column="2" bordered>
              <a-descriptions-item label="ID">{{ selectedCategory.id }}</a-descriptions-item>
              <a-descriptions-item label="名称">{{ selectedCategory.name }}</a-descriptions-item>
              <a-descriptions-item label="编码">{{ selectedCategory.code || '-' }}</a-descriptions-item>
              <a-descriptions-item label="层级">{{ selectedCategory.level }}</a-descriptions-item>
              <a-descriptions-item label="路径">{{ selectedCategory.path }}</a-descriptions-item>
              <a-descriptions-item label="排序">{{ selectedCategory.sort_order }}</a-descriptions-item>
              <a-descriptions-item label="状态">
                <a-tag :color="selectedCategory.is_active ? 'green' : 'red'">
                  {{ selectedCategory.is_active ? '启用' : '停用' }}
                </a-tag>
              </a-descriptions-item>
              <a-descriptions-item label="创建时间">
                {{ formatDate(selectedCategory.created_at) }}
              </a-descriptions-item>
            </a-descriptions>

            <template v-if="currentSummary">
              <a-divider />
              <h3>节点汇总（含所有子节点）</h3>
              <a-row :gutter="16">
                <a-col :span="8">
                  <a-statistic title="条目总数" :value="currentSummary.total_count" />
                </a-col>
                <a-col :span="8">
                  <a-statistic title="未读数量" :value="currentSummary.unread_count" :value-style="{ color: '#f5222d' }" />
                </a-col>
                <a-col :span="8">
                  <a-statistic title="待复核数量" :value="currentSummary.pending_count" :value-style="{ color: '#fa8c16' }" />
                </a-col>
              </a-row>
            </template>

            <a-divider />
            <a-space>
              <a-button type="primary" @click="openEditModal">
                <EditOutlined /> 编辑
              </a-button>
              <a-button @click="openMoveModal">
                <SwapOutlined /> 移动
              </a-button>
              <a-button @click="openMergeModal">
                <MergeCellsOutlined /> 合并
              </a-button>
              <a-button @click="openCopyModal">
                <CopyOutlined /> 复制到其他部门
              </a-button>
              <a-popconfirm
                v-if="selectedCategory.is_active"
                title="确定要停用该分类吗？"
                ok-text="确定"
                cancel-text="取消"
                @confirm="handleDeactivate"
              >
                <a-button danger>
                  <StopOutlined /> 停用
                </a-button>
              </a-popconfirm>
              <a-popconfirm
                v-else
                title="确定要启用该分类吗？"
                ok-text="确定"
                cancel-text="取消"
                @confirm="handleActivate"
              >
                <a-button type="primary" ghost>
                  <PlayCircleOutlined /> 启用
                </a-button>
              </a-popconfirm>
              <a-popconfirm
                title="删除后无法恢复，确定要删除吗？"
                ok-text="确定"
                ok-type="danger"
                cancel-text="取消"
                @confirm="handleDelete"
              >
                <a-button danger>
                  <DeleteOutlined /> 删除
                </a-button>
              </a-popconfirm>
            </a-space>
          </template>
          <template v-else>
            <a-empty description="请选择一个分类节点查看详情" />
          </template>
        </a-card>
      </a-col>
    </a-row>

    <a-modal
      v-model:open="editModalVisible"
      :title="editMode ? '编辑分类' : '新增分类'"
      @ok="handleEditSubmit"
      :confirm-loading="submitting"
    >
      <a-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        layout="vertical"
      >
        <a-form-item label="名称" name="name">
          <a-input v-model:value="formData.name" placeholder="请输入分类名称" />
        </a-form-item>
        <a-form-item label="编码" name="code">
          <a-input v-model:value="formData.code" placeholder="请输入分类编码（可选）" />
        </a-form-item>
        <a-form-item label="排序" name="sort_order">
          <a-input-number v-model:value="formData.sort_order" style="width: 100%" :min="0" />
        </a-form-item>
      </a-form>
    </a-modal>

    <a-modal
      v-model:open="moveModalVisible"
      title="移动分类"
      @ok="handleMoveSubmit"
      :confirm-loading="submitting"
    >
      <p v-if="selectedCategory">
        确定要将 <strong>{{ selectedCategory.name }}</strong> 移动到以下分类下吗？
      </p>
      <a-form layout="vertical">
        <a-form-item label="目标父分类" required>
          <a-tree-select
            v-model:value="moveTargetId"
            :tree-data="treeSelectData"
            placeholder="请选择目标父分类"
            style="width: 100%"
            :field-names="{ children: 'children', label: 'name', value: 'id' }"
            tree-default-expand-all
            allow-clear
          />
        </a-form-item>
      </a-form>
    </a-modal>

    <a-modal
      v-model:open="mergeModalVisible"
      title="合并分类"
      @ok="handleMergeSubmit"
      :confirm-loading="submitting"
    >
      <p v-if="selectedCategory">
        确定要将 <strong>{{ selectedCategory.name }}</strong> 及其所有子节点的制度条目合并到以下目录吗？
        原分类将被删除。
      </p>
      <a-form layout="vertical">
        <a-form-item label="目标分类" required>
          <a-tree-select
            v-model:value="mergeTargetId"
            :tree-data="treeSelectData"
            placeholder="请选择目标分类"
            style="width: 100%"
            :field-names="{ children: 'children', label: 'name', value: 'id' }"
            tree-default-expand-all
          />
        </a-form-item>
      </a-form>
    </a-modal>

    <a-modal
      v-model:open="copyModalVisible"
      title="复制到其他部门"
      @ok="handleCopySubmit"
      :confirm-loading="submitting"
    >
      <p v-if="selectedCategory">
        确定要将 <strong>{{ selectedCategory.name }}</strong> 及其子树复制到以下目标吗？
      </p>
      <a-form layout="vertical">
        <a-form-item label="目标责任小组" required>
          <a-select
            v-model:value="copyTargetGroupId"
            placeholder="请选择目标部门"
            style="width: 100%"
          >
            <a-select-option
              v-for="group in groupList"
              :key="group.id"
              :value="group.id"
            >
              {{ group.name }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="目标父分类（可选）">
          <a-tree-select
            v-model:value="copyTargetParentId"
            :tree-data="groupTreeSelectData"
            placeholder="不选则作为根节点"
            style="width: 100%"
            :field-names="{ children: 'children', label: 'name', value: 'id' }"
            tree-default-expand-all
            allow-clear
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import {
  EditOutlined,
  SwapOutlined,
  MergeCellsOutlined,
  CopyOutlined,
  StopOutlined,
  PlayCircleOutlined,
  DeleteOutlined
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import CategoryTree from '@/components/CategoryTree.vue'
import { useCategoryStore } from '@/stores/category'
import { getNodeSummary, type NodeSummary } from '@/api/summary'
import { type CategoryCreate, type CategoryUpdate } from '@/api/category'
import { useUserStore } from '@/stores/user'
import { getGroups } from '@/api/groups'
import type { Rule } from 'ant-design-vue/es/form'

const userStore = useUserStore()
const categoryStore = useCategoryStore()

const treeRef = ref()
const formRef = ref()
const loading = ref(false)
const submitting = ref(false)
const editModalVisible = ref(false)
const moveModalVisible = ref(false)
const mergeModalVisible = ref(false)
const copyModalVisible = ref(false)
const editMode = ref(false)
const editId = ref<number | null>(null)
const moveTargetId = ref<number | null>(null)
const mergeTargetId = ref<number | null>(null)
const copyTargetGroupId = ref<number | null>(null)
const copyTargetParentId = ref<number | null>(null)
const groupList = ref<any[]>([])
const currentSummary = ref<NodeSummary | null>(null)

const selectedCategory = computed(() => categoryStore.selectedCategory)

const formData = reactive<CategoryCreate>({
  name: '',
  code: '',
  parent_id: undefined,
  sort_order: 0
})

const formRules: Record<string, Rule[]> = {
  name: [{ required: true, message: '请输入分类名称' }]
}

const treeSelectData = computed(() => {
  const filterActive = (nodes: any[]): any[] => {
    return nodes
      .filter((n: any) => n.is_active)
      .map((n: any) => ({
        ...n,
        disabled: disabledNodeIds.value.includes(n.id),
        children: n.children ? filterActive(n.children) : undefined
      }))
  }
  return filterActive(categoryStore.treeData)
})

const disabledNodeIds = computed(() => {
  const collectIds = (nodes: any[]): number[] => {
    let ids: number[] = []
    for (const n of nodes) {
      ids.push(n.id)
      if (n.children) ids = ids.concat(collectIds(n.children))
    }
    return ids
  }
  if (!selectedCategory.value) return []
  return collectIds([selectedCategory.value])
})

const groupTreeSelectData = computed(() => {
  if (!copyTargetGroupId.value) return []
  const filterByGroup = (nodes: any[]): any[] => {
    return nodes
      .filter((n: any) => n.group_id === copyTargetGroupId.value || n.group_id === null)
      .map((n: any) => ({
        ...n,
        children: n.children ? filterByGroup(n.children) : undefined
      }))
  }
  return filterByGroup(categoryStore.treeData)
})

const loadGroups = async () => {
  try {
    const res = await getGroups()
    if (res.code === 200) {
      groupList.value = res.data
    }
  } catch (e) {
    console.error('Load groups failed:', e)
  }
}

const loadSummary = async () => {
  if (!categoryStore.selectedCategoryId) {
    currentSummary.value = null
    return
  }
  try {
    const res = await getNodeSummary(categoryStore.selectedCategoryId)
    if (res.code === 200) {
      currentSummary.value = res.data
    }
  } catch (e) {
    console.error('Load summary failed:', e)
  }
}

const handleCategorySelect = () => {
  loadSummary()
}

const openEditModal = () => {
  editMode.value = true
  editId.value = selectedCategory.value?.id || null
  formData.name = selectedCategory.value?.name || ''
  formData.code = selectedCategory.value?.code || ''
  formData.sort_order = selectedCategory.value?.sort_order || 0
  editModalVisible.value = true
}

const openAddModal = (node?: any, parentId?: number) => {
  editMode.value = false
  editId.value = null
  formData.name = ''
  formData.code = ''
  formData.parent_id = parentId
  formData.sort_order = 0
  editModalVisible.value = true
}

const openMoveModal = () => {
  moveTargetId.value = null
  moveModalVisible.value = true
}

const openMergeModal = () => {
  mergeTargetId.value = null
  mergeModalVisible.value = true
}

const openCopyModal = () => {
  copyTargetGroupId.value = null
  copyTargetParentId.value = null
  copyModalVisible.value = true
}

const handleEditSubmit = async () => {
  try {
    await formRef.value.validate()
    submitting.value = true
    if (editMode.value && editId.value) {
      const data: CategoryUpdate = {
        name: formData.name,
        code: formData.code,
        sort_order: formData.sort_order
      }
      const res = await categoryStore.update(editId.value, data)
      if (res) {
        message.success('更新成功')
        editModalVisible.value = false
        loadSummary()
      }
    } else {
      const res = await categoryStore.create(formData)
      if (res) {
        message.success('创建成功')
        editModalVisible.value = false
      }
    }
  } finally {
    submitting.value = false
  }
}

const handleMoveSubmit = async () => {
  if (!selectedCategory.value || !moveTargetId.value) return
  submitting.value = true
  try {
    const success = await categoryStore.move(selectedCategory.value.id, moveTargetId.value)
    if (success) {
      moveModalVisible.value = false
      loadSummary()
    }
  } finally {
    submitting.value = false
  }
}

const handleMergeSubmit = async () => {
  if (!selectedCategory.value || !mergeTargetId.value) return
  submitting.value = true
  try {
    const success = await categoryStore.merge(selectedCategory.value.id, mergeTargetId.value)
    if (success) {
      mergeModalVisible.value = false
      loadSummary()
    }
  } finally {
    submitting.value = false
  }
}

const handleCopySubmit = async () => {
  if (!selectedCategory.value || !copyTargetGroupId.value) return
  submitting.value = true
  try {
    const success = await categoryStore.copy(
      selectedCategory.value.id,
      copyTargetGroupId.value,
      copyTargetParentId.value || undefined
    )
    if (success) {
      copyModalVisible.value = false
    }
  } finally {
    submitting.value = false
  }
}

const handleDeactivate = async () => {
  if (!selectedCategory.value) return
  const success = await categoryStore.deactivate(selectedCategory.value.id)
  if (success) {
    loadSummary()
  }
}

const handleActivate = async () => {
  if (!selectedCategory.value) return
  const success = await categoryStore.update(selectedCategory.value.id, { is_active: true })
  if (success) {
    loadSummary()
  }
}

const handleDelete = async () => {
  if (!selectedCategory.value) return
  const success = await categoryStore.remove(selectedCategory.value.id)
  if (success) {
    currentSummary.value = null
  }
}

const formatDate = (date: string) => {
  return new Date(date).toLocaleString('zh-CN')
}

const handleOpenEditModal = (e: CustomEvent) => {
  const { node, parentId } = e.detail
  if (node) {
    categoryStore.setSelected(node.id)
    openEditModal()
  } else {
    openAddModal(null, parentId)
  }
}

const handleOpenMoveDialog = (e: CustomEvent) => {
  const { node } = e.detail
  categoryStore.setSelected(node.id)
  openMoveModal()
}

const handleOpenMergeDialog = (e: CustomEvent) => {
  const { node } = e.detail
  categoryStore.setSelected(node.id)
  openMergeModal()
}

const handleOpenCopyDialog = (e: CustomEvent) => {
  const { node } = e.detail
  categoryStore.setSelected(node.id)
  openCopyModal()
}

onMounted(async () => {
  await categoryStore.fetchTree(true)
  loadGroups()
  document.addEventListener('openEditModal', handleOpenEditModal as EventListener)
  document.addEventListener('openMoveDialog', handleOpenMoveDialog as EventListener)
  document.addEventListener('openMergeDialog', handleOpenMergeDialog as EventListener)
  document.addEventListener('openCopyDialog', handleOpenCopyDialog as EventListener)
})

onUnmounted(() => {
  document.removeEventListener('openEditModal', handleOpenEditModal as EventListener)
  document.removeEventListener('openMoveDialog', handleOpenMoveDialog as EventListener)
  document.removeEventListener('openMergeDialog', handleOpenMergeDialog as EventListener)
  document.removeEventListener('openCopyDialog', handleOpenCopyDialog as EventListener)
})
</script>

<style scoped>
.category-management-page {
  padding: 0;
}

.tree-card,
.detail-card {
  height: calc(100vh - 144px);
  display: flex;
  flex-direction: column;
}

.tree-card :deep(.ant-card-body),
.detail-card :deep(.ant-card-body) {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.detail-card h3 {
  margin: 0 0 16px;
}
</style>
