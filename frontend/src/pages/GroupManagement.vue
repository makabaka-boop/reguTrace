<template>
  <div class="group-management-page">
    <a-card :bordered="false">
      <template #extra>
        <a-button type="primary" @click="openCreateModal">
          <PlusOutlined /> 新增小组
        </a-button>
        <a-button @click="loadData">
          <ReloadOutlined /> 刷新
        </a-button>
      </template>
      <a-table
        :columns="columns"
        :data-source="groupList"
        :loading="loading"
        row-key="id"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'action'">
            <a-space>
              <a-button size="small" @click="handleEdit(record)">编辑</a-button>
              <a-popconfirm
                title="删除后无法恢复，确定要删除吗？"
                ok-text="确定"
                ok-type="danger"
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
      v-model:open="modalVisible"
      :title="editMode ? '编辑小组' : '新增小组'"
      @ok="handleSubmit"
      :confirm-loading="submitting"
    >
      <a-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        layout="vertical"
      >
        <a-form-item label="小组名称" name="name">
          <a-input v-model:value="formData.name" placeholder="请输入小组名称" />
        </a-form-item>
        <a-form-item label="描述" name="description">
          <a-textarea v-model:value="formData.description" :rows="3" placeholder="请输入描述" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { PlusOutlined, ReloadOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { useUserStore } from '@/stores/user'
import { getGroups, createGroup, updateGroup, deleteGroup, type Group } from '@/api/groups'
import type { Rule } from 'ant-design-vue/es/form'

const userStore = useUserStore()

const formRef = ref()
const loading = ref(false)
const submitting = ref(false)
const modalVisible = ref(false)
const editMode = ref(false)
const editId = ref<number | null>(null)
const groupList = ref<Group[]>([])

const formData = reactive({
  name: '',
  description: ''
})

const formRules: Record<string, Rule[]> = {
  name: [{ required: true, message: '请输入小组名称' }]
}

const columns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 80 },
  { title: '小组名称', dataIndex: 'name', key: 'name' },
  { title: '描述', dataIndex: 'description', key: 'description' },
  { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 180 },
  { title: '操作', key: 'action', width: 150, fixed: 'right' }
]

const loadData = async () => {
  loading.value = true
  try {
    const res = await getGroups()
    if (res.code === 200) {
      groupList.value = res.data
    }
  } finally {
    loading.value = false
  }
}

const openCreateModal = () => {
  editMode.value = false
  editId.value = null
  formData.name = ''
  formData.description = ''
  modalVisible.value = true
}

const handleEdit = (record: any) => {
  editMode.value = true
  editId.value = record.id
  formData.name = record.name
  formData.description = record.description || ''
  modalVisible.value = true
}

const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    submitting.value = true
    
    let res
    if (editMode.value && editId.value) {
      res = await updateGroup(editId.value, formData)
    } else {
      res = await createGroup(formData)
    }
    
    if (res.code === 200) {
      message.success(editMode.value ? '更新成功' : '创建成功')
      modalVisible.value = false
      loadData()
    }
  } finally {
    submitting.value = false
  }
}

const handleDelete = async (id: number) => {
  try {
    const res = await deleteGroup(id)
    if (res.code === 200) {
      message.success('删除成功')
      loadData()
    }
  } catch (e) {
    message.error('删除失败')
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.group-management-page {
  padding: 0;
}
</style>
