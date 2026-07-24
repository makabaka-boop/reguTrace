<template>
  <div class="category-tree-wrapper" @click="handleClickOutside">
    <div class="tree-header">
      <a-input-search
        v-model:value="searchValue"
        placeholder="搜索分类..."
        allow-clear
        style="margin-bottom: 12px"
      />
      <div class="tree-actions">
        <a-space>
          <a-button
            v-if="showAddRoot && userStore.hasRole('admin')"
            type="primary"
            size="small"
            @click="handleAddRoot"
          >
            <PlusOutlined /> 新增根节点
          </a-button>
          <a-button
            v-if="userStore.hasRole('admin')"
            size="small"
            @click="toggleIncludeInactive"
          >
            <component :is="includeInactive ? EyeInvisibleOutlined : EyeOutlined" />
            {{ includeInactive ? '隐藏停用' : '显示停用' }}
          </a-button>
          <a-button size="small" @click="refreshTree">
            <ReloadOutlined :spin="loading" /> 刷新
          </a-button>
        </a-space>
      </div>
    </div>

    <a-tree
      ref="treeRef"
      :tree-data="treeNodes"
      v-model:expandedKeys="expandedKeys"
      v-model:selectedKeys="selectedKeys"
      :draggable="draggable && userStore.hasRole('admin')"
      :block-node="true"
      @select="handleSelect"
      @drop="handleDrop"
      @rightClick="handleRightClick"
      class="category-tree"
    >
      <template #title="{ data }">
        <span
          class="tree-node-title"
          :class="{ 'node-inactive': !data.is_active }"
        >
          <component :is="data.children?.length ? FolderOpenOutlined : FileOutlined" />
          <span class="node-name">{{ data.name }}</span>
          <template v-if="showSummary && nodeSummaries[data.id]">
            <a-tag color="blue" size="small">
              {{ nodeSummaries[data.id].total_count }}
            </a-tag>
            <a-tag
              v-if="nodeSummaries[data.id].unread_count > 0"
              color="red"
              size="small"
            >
              {{ nodeSummaries[data.id].unread_count }}
            </a-tag>
            <a-tag
              v-if="nodeSummaries[data.id].pending_count > 0"
              color="orange"
              size="small"
            >
              {{ nodeSummaries[data.id].pending_count }}
            </a-tag>
          </template>
          <span v-if="!data.is_active" class="inactive-badge">已停用</span>
        </span>
      </template>
    </a-tree>

    <a-dropdown
      v-model:open="contextMenuVisible"
      :trigger="[]"
      :overlayStyle="{ left: contextMenuPosition.x + 'px', top: contextMenuPosition.y + 'px', position: 'fixed' }"
    >
      <template #overlay>
        <a-menu @click="handleContextMenuClick">
          <a-menu-item key="view" v-if="!userStore.hasRole('admin')">
            <EyeOutlined /> 查看
          </a-menu-item>
          <a-menu-item key="add" v-if="userStore.hasRole('admin')">
            <PlusOutlined /> 新增子节点
          </a-menu-item>
          <a-menu-item key="edit" v-if="userStore.hasRole('admin')">
            <EditOutlined /> 编辑
          </a-menu-item>
          <a-menu-item key="move" v-if="userStore.hasRole('admin')">
            <SwapOutlined /> 移动到...
          </a-menu-item>
          <a-menu-item key="merge" v-if="userStore.hasRole('admin')">
            <MergeCellsOutlined /> 合并到...
          </a-menu-item>
          <a-menu-item key="copy" v-if="userStore.hasRole('admin')">
            <CopyOutlined /> 复制到其他部门
          </a-menu-item>
          <a-menu-divider v-if="userStore.hasRole('admin')" />
          <a-menu-item
            key="deactivate"
            v-if="userStore.hasRole('admin') && contextNode?.is_active"
          >
            <StopOutlined /> 停用
          </a-menu-item>
          <a-menu-item
            key="activate"
            v-if="userStore.hasRole('admin') && !contextNode?.is_active"
          >
            <PlayCircleOutlined /> 启用
          </a-menu-item>
          <a-menu-item
            key="delete"
            v-if="userStore.hasRole('admin')"
            danger
          >
            <DeleteOutlined /> 删除
          </a-menu-item>
        </a-menu>
      </template>
      <div />
    </a-dropdown>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import {
  PlusOutlined,
  ReloadOutlined,
  EyeOutlined,
  EyeInvisibleOutlined,
  FolderOpenOutlined,
  FileOutlined,
  EditOutlined,
  SwapOutlined,
  MergeCellsOutlined,
  CopyOutlined,
  StopOutlined,
  PlayCircleOutlined,
  DeleteOutlined
} from '@ant-design/icons-vue'
import { Modal, message } from 'ant-design-vue'
import { useCategoryStore } from '@/stores/category'
import { useUserStore } from '@/stores/user'
import { getAllNodesSummary, type NodeSummary } from '@/api/summary'
import type { CategoryNode } from '@/api/category'

interface Props {
  showAddRoot?: boolean
  draggable?: boolean
  showSummary?: boolean
  showInactiveOption?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showAddRoot: true,
  draggable: true,
  showSummary: true,
  showInactiveOption: true
})

const emit = defineEmits<{
  select: [node: CategoryNode | null]
  nodeChange: []
}>()

const categoryStore = useCategoryStore()
const userStore = useUserStore()

const treeRef = ref()
const searchValue = ref('')
const expandedKeys = ref<(string | number)[]>([])
const selectedKeys = ref<(string | number)[]>([])
const includeInactive = ref(false)
const loading = computed(() => categoryStore.loading)
const contextMenuVisible = ref(false)
const contextMenuPosition = ref({ x: 0, y: 0 })
const contextNode = ref<CategoryNode | null>(null)
const nodeSummaries = ref<Record<number, NodeSummary>>({})

const treeNodes = computed(() => {
  return transformTreeData(categoryStore.treeData)
})

const transformTreeData = (nodes: CategoryNode[]): any[] => {
  const keyword = searchValue.value?.trim()?.toLowerCase()
  if (!keyword) {
    return nodes
      .filter(node => includeInactive.value || node.is_active)
      .map(node => ({
        ...node,
        key: node.id,
        title: node.name,
        data: node,
        children: node.children ? transformTreeData(node.children) : undefined,
        disabled: !node.is_active && !includeInactive.value
      }))
  }
  const filterNodes = (list: CategoryNode[]): any[] => {
    const result: any[] = []
    for (const node of list) {
      if (!(includeInactive.value || node.is_active)) continue
      const nameMatch = node.name.toLowerCase().includes(keyword)
      const childNodes = node.children ? filterNodes(node.children) : []
      if (nameMatch || childNodes.length > 0) {
        result.push({
          ...node,
          key: node.id,
          title: node.name,
          data: node,
          children: childNodes.length > 0 ? childNodes : undefined,
          disabled: !node.is_active && !includeInactive.value
        })
      }
    }
    return result
  }
  return filterNodes(nodes)
}

const loadSummaries = async () => {
  if (!props.showSummary) return
  try {
    const res = await getAllNodesSummary()
    if (res.code === 200 && res.data) {
      const map: Record<number, NodeSummary> = {}
      res.data.forEach((s: NodeSummary) => {
        map[s.category_id] = s
      })
      nodeSummaries.value = map
    }
  } catch (e) {
    console.error('Load summaries failed:', e)
  }
}

const refreshTree = async () => {
  await categoryStore.fetchTree(includeInactive.value)
  await loadSummaries()
}

const toggleIncludeInactive = () => {
  includeInactive.value = !includeInactive.value
  refreshTree()
}

const handleSelect = (keys: (string | number)[], info: any) => {
  selectedKeys.value = keys
  if (keys.length > 0) {
    const id = Number(keys[0])
    categoryStore.setSelected(id)
    emit('select', findNodeById(categoryStore.treeData, id))
  } else {
    categoryStore.setSelected(null)
    emit('select', null)
  }
}

const findNodeById = (nodes: CategoryNode[], id: number): CategoryNode | null => {
  for (const node of nodes) {
    if (node.id === id) return node
    if (node.children) {
      const found = findNodeById(node.children, id)
      if (found) return found
    }
  }
  return null
}

const handleDrop = async (info: any) => {
  const dragNode = info.dragNode
  const dropNode = info.node
  const dropPosition = info.dropPosition

  if (dropPosition !== 0) {
    message.warning('只能作为子节点移动')
    return
  }

  const dragId = Number(dragNode.key)
  const targetParentId = Number(dropNode.key)

  if (dragId === targetParentId) {
    message.warning('不能移动到自身')
    return
  }

  Modal.confirm({
    title: '确认移动',
    content: `确定要将「${dragNode.dataRef.name}」移动到「${dropNode.dataRef.name}」下吗？`,
    async onOk() {
      const success = await categoryStore.move(dragId, targetParentId)
      if (success) {
        await loadSummaries()
        emit('nodeChange')
      }
    }
  })
}

const handleRightClick = ({ event, node }: any) => {
  event.preventDefault()
  contextNode.value = node.dataRef
  contextMenuPosition.value = { x: event.clientX, y: event.clientY }
  contextMenuVisible.value = true
}

const handleClickOutside = () => {
  if (contextMenuVisible.value) {
    contextMenuVisible.value = false
  }
}

const handleContextMenuClick = ({ key }: { key: string }) => {
  contextMenuVisible.value = false
  if (!contextNode.value) return

  const node = contextNode.value
  switch (key) {
    case 'view':
      selectedKeys.value = [node.id]
      categoryStore.setSelected(node.id)
      emit('select', node)
      break
    case 'add':
      emitOpenEditModal(null, node.id)
      break
    case 'edit':
      emitOpenEditModal(node)
      break
    case 'move':
      emitMoveDialog(node)
      break
    case 'merge':
      emitMergeDialog(node)
      break
    case 'copy':
      emitCopyDialog(node)
      break
    case 'deactivate':
      handleDeactivate(node.id)
      break
    case 'activate':
      handleActivate(node.id)
      break
    case 'delete':
      handleDelete(node.id)
      break
  }
}

const handleAddRoot = () => {
  emitOpenEditModal()
}

const emitOpenEditModal = (node?: CategoryNode | null, parentId?: number) => {
  const e = new CustomEvent('openEditModal', {
    detail: { node, parentId },
    bubbles: true
  })
  document.dispatchEvent(e)
}

const emitMoveDialog = (node: CategoryNode) => {
  const e = new CustomEvent('openMoveDialog', {
    detail: { node },
    bubbles: true
  })
  document.dispatchEvent(e)
}

const emitMergeDialog = (node: CategoryNode) => {
  const e = new CustomEvent('openMergeDialog', {
    detail: { node },
    bubbles: true
  })
  document.dispatchEvent(e)
}

const emitCopyDialog = (node: CategoryNode) => {
  const e = new CustomEvent('openCopyDialog', {
    detail: { node },
    bubbles: true
  })
  document.dispatchEvent(e)
}

const handleDeactivate = async (id: number) => {
  Modal.confirm({
    title: '确认停用',
    content: '停用后该分类及其子分类将不再显示，确定要停用吗？',
    async onOk() {
      const success = await categoryStore.deactivate(id)
      if (success) {
        await loadSummaries()
        emit('nodeChange')
      }
    }
  })
}

const handleActivate = async (id: number) => {
  Modal.confirm({
    title: '确认启用',
    content: '确定要启用该分类吗？',
    async onOk() {
      const success = await categoryStore.update(id, { is_active: true })
      if (success) {
        await loadSummaries()
        emit('nodeChange')
      }
    }
  })
}

const handleDelete = async (id: number) => {
  Modal.confirm({
    title: '确认删除',
    content: '删除后无法恢复，该目录下的制度条目将一并删除，确定要删除吗？',
    okType: 'danger',
    async onOk() {
      const success = await categoryStore.remove(id)
      if (success) {
        await loadSummaries()
        emit('nodeChange')
      }
    }
  })
}

watch(searchValue, (val) => {
  if (!val) return
  const expandIds = findExpandIds(categoryStore.treeData, val)
  expandedKeys.value = expandIds.map(id => String(id))
})

const findExpandIds = (nodes: CategoryNode[], keyword: string): number[] => {
  let ids: number[] = []
  for (const node of nodes) {
    if (node.name.includes(keyword) && node.parent_id) {
      ids.push(node.parent_id)
    }
    if (node.children) {
      const childIds = findExpandIds(node.children, keyword)
      if (childIds.length > 0) {
        ids.push(node.id, ...childIds)
      }
    }
  }
  return [...new Set(ids)]
}

onMounted(async () => {
  await refreshTree()
})

defineExpose({
  refresh: refreshTree,
  clearSelection: () => {
    selectedKeys.value = []
    categoryStore.setSelected(null)
  },
  reloadSummaries: loadSummaries
})
</script>

<style scoped>
.category-tree-wrapper {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.tree-header {
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
  margin-bottom: 12px;
}

.tree-actions {
  margin-top: 8px;
}

.category-tree {
  flex: 1;
  overflow-y: auto;
  padding: 4px;
}

.tree-node-title {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
  padding: 4px 0;
}

.tree-node-title :deep(.ant-tag) {
  font-size: 10px;
  padding: 0 4px;
  height: 18px;
  line-height: 16px;
}

.node-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.node-inactive {
  color: #999;
  text-decoration: line-through;
}

.inactive-badge {
  font-size: 10px;
  color: #999;
  background: #f5f5f5;
  padding: 0 4px;
  border-radius: 2px;
}

:deep(.ant-tree-node-selected .ant-tree-node-content-wrapper) {
  background: #e6f7ff !important;
}
</style>
