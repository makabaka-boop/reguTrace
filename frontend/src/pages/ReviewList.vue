<template>
  <div class="review-page">
    <a-row :gutter="[16, 16]" style="margin-bottom: 16px">
      <a-col :span="6">
        <a-card size="small">
          <a-statistic
            title="待复核"
            :value="stats.pending_count"
            :value-style="{ color: '#fa8c16' }"
          />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card size="small">
          <a-statistic
            title="即将到期"
            :value="stats.upcoming_count"
            :value-style="{ color: '#faad14' }"
          />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card size="small">
          <a-statistic
            title="已到期"
            :value="stats.overdue_count"
            :value-style="{ color: '#f5222d' }"
          />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card size="small">
          <a-statistic
            title="已通过"
            :value="stats.approved_count"
            :value-style="{ color: '#52c41a' }"
          />
        </a-card>
      </a-col>
    </a-row>

    <a-card :bordered="false">
      <template #extra>
        <a-space>
          <a-select
            v-model:value="activeTab"
            style="width: 150px"
            @change="handleTabChange"
          >
            <a-select-option value="pending">待复核</a-select-option>
            <a-select-option value="approved">已通过</a-select-option>
            <a-select-option value="rejected">已驳回</a-select-option>
          </a-select>
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
          <a-button
            type="primary"
            :disabled="selectedRowKeys.length === 0"
            @click="batchApprove"
          >
            <CheckOutlined /> 批量通过
          </a-button>
          <a-button
            danger
            :disabled="selectedRowKeys.length === 0"
            @click="batchReject"
          >
            <CloseOutlined /> 批量驳回
          </a-button>
          <a-button
            type="primary"
            ghost
            @click="handleExport"
          >
            <DownloadOutlined /> 导出清单
          </a-button>
          <a-button @click="loadData">
            <ReloadOutlined /> 刷新
          </a-button>
        </a-space>
      </template>

      <a-table
        :columns="columns"
        :data-source="knowledgeList"
        :loading="loading"
        :pagination="pagination"
        :row-selection="rowSelection"
        row-key="id"
        @change="handleTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'title'">
            <a @click="viewDetail(record)">{{ record.title }}</a>
          </template>
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
          <template v-else-if="column.key === 'action'">
            <a-space>
              <a-button size="small" @click="viewDetail(record)">查看</a-button>
              <a-button
                size="small"
                type="primary"
                v-if="record.review_status === 'pending'"
                @click="openApproveModal(record)"
              >
                通过
              </a-button>
              <a-button
                size="small"
                danger
                v-if="record.review_status === 'pending'"
                @click="openRejectModal(record)"
              >
                驳回
              </a-button>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <a-modal
      v-model:open="detailModalVisible"
      title="制度详情"
      width="800px"
    >
      <template #footer v-if="currentDetail && currentDetail.review_status === 'pending'">
        <a-button @click="openRejectModal(currentDetail)">驳回</a-button>
        <a-button type="primary" @click="openApproveModal(currentDetail)">通过</a-button>
      </template>
      <div v-if="currentDetail" class="detail-content">
        <h2>{{ currentDetail.title }}</h2>
        <div class="detail-meta">
          <a-space>
            <span>分类: {{ currentDetail.category_name }}</span>
            <span>提交人: {{ currentDetail.submitter_name }}</span>
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
      </div>
    </a-modal>

    <a-modal
      v-model:open="approveModalVisible"
      title="确认通过"
      @ok="handleApprove"
      :confirm-loading="submitting"
    >
      <p>确定要通过这条制度条目吗？</p>
      <a-form layout="vertical">
        <a-form-item label="修改分类（可选）">
          <a-tree-select
            v-model:value="approveForm.new_category_id"
            :tree-data="treeSelectData"
            placeholder="如无需修改则留空"
            style="width: 100%"
            :field-names="{ children: 'children', label: 'name', value: 'id' }"
            tree-default-expand-all
            allow-clear
          />
        </a-form-item>
        <a-form-item label="备注（可选）">
          <a-textarea v-model:value="approveForm.remark" :rows="3" placeholder="请输入备注" />
        </a-form-item>
      </a-form>
    </a-modal>

    <a-modal
      v-model:open="rejectModalVisible"
      title="确认驳回"
      @ok="handleReject"
      :confirm-loading="submitting"
    >
      <p>确定要驳回这条制度条目吗？</p>
      <a-form layout="vertical">
        <a-form-item label="驳回原因" required>
          <a-textarea v-model:value="rejectForm.remark" :rows="3" placeholder="请输入驳回原因" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import {
  CheckOutlined,
  CloseOutlined,
  DownloadOutlined,
  ReloadOutlined
} from '@ant-design/icons-vue'
import { Modal, message } from 'ant-design-vue'
import { useUserStore } from '@/stores/user'
import { useCategoryStore } from '@/stores/category'
import {
  getPendingList,
  approveKnowledge,
  rejectKnowledge,
  batchApprove,
  batchReject,
  getStatistics,
  type KnowledgeItem,
  type KnowledgeListResponse
} from '@/api/review'
import { getKnowledgeList } from '@/api/knowledge'
import { type ReviewRequest, type ReviewBatchRequest } from '@/api/review'

const userStore = useUserStore()
const categoryStore = useCategoryStore()

const loading = ref(false)
const submitting = ref(false)
const activeTab = ref('pending')
const expiryFilter = ref<string | undefined>()
const knowledgeList = ref<KnowledgeItem[]>([])
const currentDetail = ref<KnowledgeItem | null>(null)
const detailModalVisible = ref(false)
const approveModalVisible = ref(false)
const rejectModalVisible = ref(false)
const selectedRowKeys = ref<number[]>([])
const currentReviewId = ref<number | null>(null)

const stats = reactive({
  pending_count: 0,
  approved_count: 0,
  rejected_count: 0,
  upcoming_count: 0,
  overdue_count: 0
})

const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total: number) => `共 ${total} 条`
})

const approveForm = reactive<ReviewRequest>({
  remark: '',
  new_category_id: undefined
})

const rejectForm = reactive<ReviewRequest>({
  remark: ''
})

const columns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 70 },
  { title: '标题', dataIndex: 'title', key: 'title', ellipsis: true },
  { title: '分类', dataIndex: 'category_name', key: 'category_name', width: 120 },
  { title: '提交人', dataIndex: 'submitter_name', key: 'submitter_name', width: 100 },
  { title: '状态', key: 'review_status', width: 90 },
  { title: '复核到期', key: 'review_expiry_status', width: 100 },
  { title: '提交时间', dataIndex: 'created_at', key: 'created_at', width: 170 },
  { title: '操作', key: 'action', width: 200, fixed: 'right' }
]

const rowSelection = {
  selectedRowKeys: selectedRowKeys,
  onChange: (keys: number[]) => {
    selectedRowKeys.value = keys
  }
}

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

const loadStats = async () => {
  getStatistics().then(res => {
    if (res.code === 200) {
      Object.assign(stats, res.data)
    }
  })
}

const loadData = async () => {
  loading.value = true
  try {
    let res
    if (activeTab.value === 'pending') {
      res = await getPendingList({
        page: pagination.current,
        page_size: pagination.pageSize,
        review_expiry_status: expiryFilter.value
      })
    } else {
      res = await getKnowledgeList({
        page: pagination.current,
        page_size: pagination.pageSize,
        review_status: activeTab.value,
        review_expiry_status: expiryFilter.value
      })
    }
    if (res.code === 200) {
      const data = res.data as KnowledgeListResponse
      knowledgeList.value = data.items
      pagination.total = data.total
    }
  } finally {
    loading.value = false
  }
}

const handleTabChange = () => {
  pagination.current = 1
  selectedRowKeys.value = []
  loadData()
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

const openApproveModal = (item: KnowledgeItem) => {
  currentReviewId.value = item.id
  approveForm.remark = ''
  approveForm.new_category_id = undefined
  approveModalVisible.value = true
  detailModalVisible.value = false
}

const openRejectModal = (item: KnowledgeItem) => {
  currentReviewId.value = item.id
  rejectForm.remark = ''
  rejectModalVisible.value = true
  detailModalVisible.value = false
}

const handleApprove = async () => {
  if (!currentReviewId.value) return
  submitting.value = true
  try {
    const data: ReviewRequest = {
      remark: approveForm.remark
    }
    if (approveForm.new_category_id) {
      data.new_category_id = approveForm.new_category_id
    }
    const res = await approveKnowledge(currentReviewId.value, data)
    if (res.code === 200) {
      message.success('已通过')
      approveModalVisible.value = false
      loadData()
      loadStats()
    }
  } finally {
    submitting.value = false
  }
}

const handleReject = async () => {
  if (!currentReviewId.value) return
  if (!rejectForm.remark) {
    message.warning('请输入驳回原因')
    return
  }
  submitting.value = true
  try {
    const res = await rejectKnowledge(currentReviewId.value, {
      remark: rejectForm.remark
    })
    if (res.code === 200) {
      message.success('已驳回')
      rejectModalVisible.value = false
      loadData()
      loadStats()
    }
  } finally {
    submitting.value = false
  }
}

const batchApprove = () => {
  if (selectedRowKeys.value.length === 0) return
  Modal.confirm({
    title: '批量通过',
    content: `确定要通过选中的 ${selectedRowKeys.value.length} 条制度条目吗？`,
    async onOk() {
      const data: ReviewBatchRequest = {
        knowledge_ids: selectedRowKeys.value
      }
      const res = await batchApprove(data)
      if (res.code === 200) {
        message.success('批量通过成功')
        selectedRowKeys.value = []
        loadData()
        loadStats()
      }
    }
  })
}

const batchReject = () => {
  if (selectedRowKeys.value.length === 0) return
  Modal.confirm({
    title: '批量驳回',
    content: `确定要驳回选中的 ${selectedRowKeys.value.length} 条制度条目吗？`,
    async onOk() {
      const data: ReviewBatchRequest = {
        knowledge_ids: selectedRowKeys.value
      }
      const res = await batchReject(data)
      if (res.code === 200) {
        message.success('批量驳回成功')
        selectedRowKeys.value = []
        loadData()
        loadStats()
      }
    }
  })
}

const handleExport = async () => {
  try {
    const res = await fetch('/api/export/knowledge', {
      headers: {
        'Authorization': `Bearer ${userStore.token}`
      }
    })
    if (res.ok) {
      const blob = await res.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `知识清单_${new Date().toISOString().slice(0, 10)}.xlsx`
      a.click()
      window.URL.revokeObjectURL(url)
      message.success('导出成功')
    }
  } catch (e) {
    message.error('导出失败')
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
  loadStats()
})
</script>

<style scoped>
.review-page {
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
</style>
