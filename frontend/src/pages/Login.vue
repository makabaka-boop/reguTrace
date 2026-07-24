<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-header">
        <BookOutlined class="logo-icon" />
        <h1>企业制度知识复核与阅读追踪系统</h1>
        <p>制度条目归口、阅读确认、到期复审闭环</p>
      </div>
      <a-form
        ref="formRef"
        :model="formData"
        :rules="rules"
        layout="vertical"
        @finish="handleLogin"
      >
        <a-form-item name="role" label="登录角色">
          <a-radio-group v-model:value="formData.role" size="large" button-style="solid">
            <a-radio-button value="admin">管理员</a-radio-button>
            <a-radio-button value="employee">员工</a-radio-button>
            <a-radio-button value="supervisor">主管</a-radio-button>
          </a-radio-group>
        </a-form-item>
        <a-form-item name="username" label="用户名">
          <a-input
            v-model:value="formData.username"
            size="large"
            placeholder="请输入用户名"
          >
            <template #prefix>
              <UserOutlined />
            </template>
          </a-input>
        </a-form-item>
        <a-form-item name="password" label="密码">
          <a-input-password
            v-model:value="formData.password"
            size="large"
            placeholder="请输入密码"
          >
            <template #prefix>
              <LockOutlined />
            </template>
          </a-input-password>
        </a-form-item>
        <a-button
          type="primary"
          html-type="submit"
          size="large"
          block
          :loading="loading"
        >
          {{ loading ? '登录中...' : '登录' }}
        </a-button>
      </a-form>
      <div class="login-tips">
        <a-divider>默认账号</a-divider>
        <a-descriptions :column="1" size="small" bordered>
          <a-descriptions-item label="管理员">admin / 123456</a-descriptions-item>
          <a-descriptions-item label="员工">employee1 / 123456</a-descriptions-item>
          <a-descriptions-item label="主管">supervisor1 / 123456</a-descriptions-item>
        </a-descriptions>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import { BookOutlined, UserOutlined, LockOutlined } from '@ant-design/icons-vue'
import { useUserStore } from '@/stores/user'
import type { Rule } from 'ant-design-vue/es/form'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const formRef = ref()
const loading = ref(false)

const formData = reactive({
  username: '',
  password: '',
  role: 'employee'
})

const rules: Record<string, Rule[]> = {
  username: [{ required: true, message: '请输入用户名' }],
  password: [{ required: true, message: '请输入密码' }],
  role: [{ required: true, message: '请选择角色' }]
}

const handleLogin = async () => {
  loading.value = true
  try {
    const success = await userStore.login({
      username: formData.username,
      password: formData.password,
      role: formData.role
    })
    if (success) {
      const redirect = route.query.redirect as string
      router.push(redirect || '/dashboard')
    }
  } catch (error) {
    message.error('登录失败，请检查用户名和密码')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.login-box {
  width: 100%;
  max-width: 420px;
  background: #fff;
  border-radius: 12px;
  padding: 40px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.logo-icon {
  font-size: 48px;
  color: #1890ff;
  margin-bottom: 12px;
}

.login-header h1 {
  margin: 0 0 8px;
  font-size: 24px;
  font-weight: 600;
  color: #333;
}

.login-header p {
  margin: 0;
  color: #999;
  font-size: 14px;
}

.login-tips {
  margin-top: 24px;
}
</style>
