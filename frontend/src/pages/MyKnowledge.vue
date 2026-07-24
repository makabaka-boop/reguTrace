<template>
  <div class="my-knowledge-page">
    <a-card :bordered="false">
      <template #extra>
        <a-space>
          <a-select
            v-model:value="expiryFilter"
            placeholder="复核到期"
            style="width: 130px"
            allow-clear
            @change="loadData"
          >
            <a-select-option value="normal">正常</a-select-option>
            <a-select-option value="upcoming">即将到期</a-select-option>
            <a-select-option value="overdue">已到期</a-select-option>
          </a-select>
          <a-button type="primary" @click="openCreateModal">
            <PlusOutlined /> 提交新制度
          </a-button>
          <a-button @click="loadData">
            <ReloadOutlined /> 刷新
          </a-button>
        </a-space>
      </template>
      <a-alert
        message="提示"
        type="info"
        show-icon
        style="margin-bottom: 16px"
      >
        这里显示您提交的所有制度条目，包括复核状态和下次复审时间。
      </a-alert>
      <a-table
        :columns="columns"
        :data-source="knowledgeList"
        :loading="loading"
        :pagination="pagination"
        row-key="id"
        @change="handleTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-else-if="column.key === 'review_status'">
            <a-tag :color="getStatusColor(record.review_status)">
              {{ getStatusLabel(record.review_status) }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'review_expiry_status'">
            <a-tag v-if="record.review_expiry_status === 'normal'" color="green">正常</a-tag>
            <a-tag v-else-if="record.review_expiry_status === 'upcoming'" color="orange">即将到期</a-tag>
            <a-tag v-else-if="record.review_expiry_status === 'overdue'" color="red">已到期</a-tag>
            <span v-else>-</span>
          </template>
          <template v-else-if="column.key === 'reject_reason'">
            <span v-if="record.review_status === 'rejected'" style="color: #f5222d">
              {{ record.reject_reason }}
            </span>
            <span v-else>-</span>
          </template>
          <template v-else-if="column.key === 'action'">
            <a-space>
              <a-button size="small" @click="viewDetail(record)">查看</a-button>
              <a-button
                size="small"
                @click="handleEdit(record)"
                v-if="record.review_status !== 'approved'"
              >
                编辑
              </a-button>
              <a-popconfirm
                title="确定要删除吗？"
                ok-text="确定"
                cancel-text="取消"
                @confirm="handleDelete(record.id)"
              >
                <a-button size="small" danger>删除</a-button>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <a-modal
      v-model:open="detailModalVisible"
      title="制度详情"
      width="800px"
      :footer="null"
    >
      <div v-if="currentDetail" class="detail-content">
        <h2>{{ currentDetail.title }}</h2>
        <div class="detail-meta">
          <a-space>
            <span>分类: {{ currentDetail.category_name }}</span>
            <span>{{ formatDate(currentDetail.created_at) }}</span>
            <a-tag :color="getStatusColor(currentDetail.review_status)">
              {{ getStatusLabel(currentDetail.review_status) }}
            </a-tag>
            <a-tag v-if="currentDetail.review_expiry_status === 'normal'" color="green">正常</a-tag>
            <a-tag v-else-if="currentDetail.review_expiry_status === 'upcoming'" color="orange">即将到期</a-tag>
            <a-tag v-else-if="currentDetail.review_expiry_status === 'overdue'" color="red">已到期</a-tag>
          </a-space>
        </div>
        <div v-if="currentDetail.next_review_date" class="detail-meta" style="margin-top: 8px">
          <span>下次复核时间: {{ formatDate(currentDetail.next_review_date) }}</span>
          <span style="margin-left: 16px">建议复核周期: {{ getCycleLabel(currentDetail.suggested_review_cycle) }}</span>
        </div>
        <a-divider />
        <div class="detail-body" v-html="currentDetail.content"></div>
        <div v-if="currentDetail.reject_reason" class="reject-reason">
          <a-alert
            message="驳回原因"
            :description="currentDetail.reject_reason"
            type="error"
            show-icon
          />
        </div>
      </div>
    </a-modal>

    <a-modal
      v-model:open="editModalVisible"
      :title="editMode ? '编辑制度' : '提交制度条目'"
      width="700px"
      @ok="handleSubmit"
      :confirm-loading="submitting"
    >
      <a-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        layout="vertical"
      >
        <a-form-item label="标题" name="title">
          <a-input v-model:value="formData.title" placeholder="请输入制度标题" />
        </a-form-item>
        <a-form-item label="分类" name="category_id">
          <a-tree-select
            v-model:value="formData.category_id"
            :tree-data="treeSelectData"
            placeholder="请选择制度目录"
            style="width: 100%"
            :field-names="{ children: 'children', label: 'name', value: 'id' }"
            tree-default-expand-all
          />
        </a-form-item>
        <a-form-item label="内容" name="content">
          <a-textarea
            v-model:value="formData.content"
            :rows="10"
            placeholder="请输入制度内容，支持HTML格式"
          />
        </a-form-item>
        <a-form-item label="建议复核周期" name="suggested_review_cycle">
          <a-select v-model:value="formData.suggested_review_cycle" style="width: 100%">
            <a-select-option value="1month">1个月</a-select-option>
            <a-select-option value="3months">3个月</a-select-option>
            <a-select-option value="6months">6个月</a-select-option>
            <a-select-option value="1year">1年</a-select-option>
            <a-select-option value="never">永不</a-select-option>
          </a-select>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { PlusOutlined, ReloadOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { useCategoryStore } from '@/stores/category'
import {
  getMyKnowledge,
  createKnowledge,
  updateKnowledge,
  deleteKnowledge,
  type KnowledgeItem,
  type KnowledgeCreate,
  type KnowledgeUpdate,
  type KnowledgeListResponse
} from '@/api/knowledge'
import type { Rule } from 'ant-design-vue/es/form'

const categoryStore = useCategoryStore()

const formRef = ref()
const loading = ref(false)
const submitting = ref(false)
const expiryFilter = ref<string | undefined>()
const knowledgeList = ref<KnowledgeItem[]>([])
const currentDetail = ref<KnowledgeItem | null>(null)
const detailModalVisible = ref(false)
const editModalVisible = ref(false)
const editMode = ref(false)
const editId = ref<number | null>(null)

const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total: number) => `共 ${total} 条`
})

const formData = reactive<KnowledgeCreate>({
  title: '',
  content: '',
  category_id: 0,
  suggested_review_cycle: '6months'
})

const formRules: Record<string, Rule[]> = {
  title: [{ required: true, message: '请输入标题' }],
  category_id: [{ required: true, message: '请选择分类' }],
  content: [{ required: true, message: '请输入内容' }]
}

const columns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 70 },
  { title: '标题', dataIndex: 'title', key: 'title', ellipsis: true },
  { title: '分类', dataIndex: 'category_name', key: 'category_name', width: 120 },
  { title: '状态', key: 'review_status', width: 90 },
  { title: '复核到期', key: 'review_expiry_status', width: 100 },
  { title: '驳回原因', key: 'reject_reason', ellipsis: true },
  { title: '提交时间', dataIndex: 'created_at', key: 'created_at', width: 170 },
  { title: '操作', key: 'action', width: 220, fixed: 'right' }
]

const treeSelectData = computed(() => {
  const filterActive = (nodes: any[]): any[] => {
    return nodes
      .filter((n: any) => n.is_active)
      .map((n: any) => ({
        ...n,
        children: n.children ? filterActive(n.children) : undefined
      }))
  }
  return filterActive(categoryStore.treeData)
})

const loadData = async () => {
  loading.value = true
  try {
    const res = await getMyKnowledge({
      page: pagination.current,
      page_size: pagination.pageSize,
      review_expiry_status: expiryFilter.value
    })
    if (res.code === 200) {
      const data = res.data as KnowledgeListResponse
      knowledgeList.value = data.items
      pagination.total = data.total
    }
  } finally {
    loading.value = false
  }
}

const handleTableChange = (p: any) => {
  pagination.current = p.current
  pagination.pageSize = p.pageSize
  loadData()
}

const viewDetail = (item: KnowledgeItem) => {
  currentDetail.value = item
  detailModalVisible.value = true
}

const openCreateModal = () => {
  editMode.value = false
  editId.value = null
  formData.title = ''
  formData.content = ''
  formData.category_id = categoryStore.selectedCategoryId || 0
  editModalVisible.value = true
}

const handleEdit = (item: KnowledgeItem) => {
  editMode.value = true
  editId.value = item.id
  formData.title = item.title
  formData.content = item.content
  formData.category_id = item.category_id
  formData.suggested_review_cycle = item.suggested_review_cycle || '6months'
  editModalVisible.value = true
}

const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    submitting.value = true
    if (editMode.value && editId.value) {
      const res = await updateKnowledge(editId.value, formData as KnowledgeUpdate)
      if (res.code === 200) {
        message.success('更新成功')
        editModalVisible.value = false
        loadData()
      }
    } else {
      const res = await createKnowledge(formData)
      if (res.code === 200) {
        message.success('提交成功，等待主管复核')
        editModalVisible.value = false
        loadData()
      }
    }
  } finally {
    submitting.value = false
  }
}

const handleDelete = async (id: number) => {
  const res = await deleteKnowledge(id)
  if (res.code === 200) {
    message.success('删除成功')
    loadData()
  }
}

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    pending: 'orange',
    approved: 'green',
    rejected: 'red'
  }
  return colors[status] || 'default'
}

const getStatusLabel = (status: string) => {
  const labels: Record<string, string> = {
    pending: '待复核',
    approved: '已通过',
    rejected: '已驳回'
  }
  return labels[status] || status
}

const getCycleLabel = (cycle?: string) => {
  const labels: Record<string, string> = {
    '1month': '1个月',
    '3months': '3个月',
    '6months': '6个月',
    '1year': '1年',
    'never': '永不'
  }
  return labels[cycle || ''] || '未设置'
}

const formatDate = (date: string) => {
  return new Date(date).toLocaleString('zh-CN')
}

onMounted(async () => {
  await categoryStore.fetchTree()
  loadData()
})
</script>

<style scoped>
.my-knowledge-page {
  padding: 0;
}

.detail-content h2 {
  margin: 0 0 12px;
}

.detail-meta {
  color: #999;
  font-size: 14px;
}

.detail-body {
  margin-top: 16px;
  line-height: 1.8;
  font-size: 15px;
}

.reject-reason {
  margin-top: 16px;
}
</style>
