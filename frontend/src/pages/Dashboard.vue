<template>
  <div class="dashboard">
    <a-row :gutter="[16, 16]">
      <a-col :xs="24" :sm="12" :lg="6">
        <a-card class="stat-card">
          <a-statistic
            title="制度条目总数"
            :value="stats.total_count"
            :value-style="{ color: '#1890ff' }"
          >
            <template #prefix>
              <BookOutlined />
            </template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :xs="24" :sm="12" :lg="6">
        <a-card class="stat-card">
          <a-statistic
            title="待我阅读"
            :value="stats.unread_count"
            :value-style="{ color: '#f5222d' }"
          >
            <template #prefix>
              <ExclamationCircleOutlined />
            </template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :xs="24" :sm="12" :lg="6" v-if="userStore.hasRole('supervisor')">
        <a-card class="stat-card">
          <a-statistic
            title="待我复核"
            :value="stats.pending_review_count"
            :value-style="{ color: '#fa8c16' }"
          >
            <template #prefix>
              <ClockCircleOutlined />
            </template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :xs="24" :sm="12" :lg="6" v-else>
        <a-card class="stat-card">
          <a-statistic
            title="我已提交"
            :value="stats.my_submitted_count"
            :value-style="{ color: '#52c41a' }"
          >
            <template #prefix>
              <FileAddOutlined />
            </template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :xs="24" :sm="12" :lg="6">
        <a-card class="stat-card">
          <a-statistic
            title="分类节点数"
            :value="stats.category_count"
            :value-style="{ color: '#722ed1' }"
          >
            <template #prefix>
              <FolderOpenOutlined />
            </template>
          </a-statistic>
        </a-card>
      </a-col>
    </a-row>

    <a-row :gutter="[16, 16]" style="margin-top: 16px" v-if="userStore.hasRole('supervisor')">
      <a-col :xs="24" :sm="12" :lg="6">
        <a-card class="stat-card">
          <a-statistic
            title="即将到期"
            :value="stats.upcoming_count"
            :value-style="{ color: '#faad14' }"
          >
            <template #prefix>
              <WarningOutlined />
            </template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :xs="24" :sm="12" :lg="6">
        <a-card class="stat-card">
          <a-statistic
            title="已到期"
            :value="stats.overdue_count"
            :value-style="{ color: '#f5222d' }"
          >
            <template #prefix>
              <AlertOutlined />
            </template>
          </a-statistic>
        </a-card>
      </a-col>
    </a-row>

    <a-row :gutter="[16, 16]" style="margin-top: 16px">
      <a-col :xs="24" :lg="12">
        <a-card title="最新制度条目" :bordered="false">
          <a-list
            :data-source="recentKnowledge"
            :loading="loading"
            item-layout="vertical"
          >
            <template #renderItem="{ item }">
              <a-list-item>
                <a-list-item-meta>
                  <template #title>
                    <a @click="viewKnowledge(item)">{{ item.title }}</a>
                    <a-tag :color="getStatusColor(item.review_status)" style="margin-left: 8px">
                      {{ getStatusLabel(item.review_status) }}
                    </a-tag>
                  </template>
                  <template #description>
                    <span>分类: {{ item.category_name }}</span>
                    <span style="margin-left: 16px">提交人: {{ item.submitter_name }}</span>
                    <span style="margin-left: 16px">{{ formatDate(item.created_at) }}</span>
                  </template>
                </a-list-item-meta>
              </a-list-item>
            </template>
          </a-list>
        </a-card>
      </a-col>
      <a-col :xs="24" :lg="12">
        <a-card title="分类概览" :bordered="false">
          <div ref="chartContainer" class="chart-container"></div>
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  BookOutlined,
  ExclamationCircleOutlined,
  ClockCircleOutlined,
  FileAddOutlined,
  FolderOpenOutlined,
  WarningOutlined,
  AlertOutlined
} from '@ant-design/icons-vue'
import { getKnowledgeList, type KnowledgeItem } from '@/api/knowledge'
import { getAllNodesSummary } from '@/api/summary'
import { getStatistics } from '@/api/review'
import { useUserStore } from '@/stores/user'
import { useCategoryStore } from '@/stores/category'
import type { KnowledgeListResponse } from '@/api/knowledge'

const router = useRouter()
const userStore = useUserStore()
const categoryStore = useCategoryStore()

const loading = ref(false)
const recentKnowledge = ref<KnowledgeItem[]>([])

const stats = reactive({
  total_count: 0,
  unread_count: 0,
  pending_review_count: 0,
  my_submitted_count: 0,
  category_count: 0,
  upcoming_count: 0,
  overdue_count: 0
})

const loadStats = async () => {
  try {
    const [summaryRes, knowledgeRes, reviewRes, categoryRes] = await Promise.all([
      getAllNodesSummary(),
      getKnowledgeList({ page_size: 1 }),
      userStore.hasRole('supervisor') ? getStatistics() : { data: { pending_count: 0 } },
      categoryStore.fetchTree()
    ])

    if (summaryRes.code === 200 && summaryRes.data) {
      stats.total_count = summaryRes.data.reduce((sum: number, s: any) => sum + s.total_count, 0)
      stats.unread_count = summaryRes.data.reduce((sum: number, s: any) => sum + s.unread_count, 0)
    }

    if (knowledgeRes.code === 200) {
      recentKnowledge.value = knowledgeRes.data.items
    }

    if (reviewRes.data) {
      stats.pending_review_count = reviewRes.data.pending_count
      stats.upcoming_count = reviewRes.data.upcoming_count || 0
      stats.overdue_count = reviewRes.data.overdue_count || 0
    }

    const countNodes = (nodes: any[]): number => {
      let count = nodes.length
      for (const n of nodes) {
        if (n.children) count += countNodes(n.children)
      }
      return count
    }
    stats.category_count = countNodes(categoryStore.treeData)
  } catch (e) {
    console.error('Load stats failed:', e)
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

const formatDate = (date: string) => {
  return new Date(date).toLocaleDateString('zh-CN')
}

const viewKnowledge = (item: KnowledgeItem) => {
  router.push({ name: 'Knowledge', query: { id: item.id } })
}

onMounted(() => {
  loadStats()
})
</script>

<style scoped>
.dashboard {
  padding: 0;
}

.stat-card {
  border-radius: 8px;
}

.chart-container {
  height: 300px;
}
</style>
