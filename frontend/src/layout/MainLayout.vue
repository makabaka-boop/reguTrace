<template>
  <a-layout style="min-height: 100vh">
    <a-layout-sider
      v-model:collapsed="collapsed"
      collapsible
      :trigger="null"
      width="240"
      class="sider"
    >
      <div class="logo">
        <BookOutlined class="logo-icon" />
        <span v-if="!collapsed">制度复核追踪</span>
      </div>
      <a-menu
        theme="dark"
        mode="inline"
        :selected-keys="[selectedKey]"
        @click="handleMenuClick"
      >
        <a-menu-item key="Dashboard" v-if="hasRole(['admin', 'employee', 'supervisor'])">
          <template #icon>
            <HomeOutlined />
          </template>
          <span>首页</span>
        </a-menu-item>
        <a-menu-item key="Knowledge" v-if="hasRole(['admin', 'employee', 'supervisor'])">
          <template #icon>
            <BookOutlined2 />
          </template>
          <span>制度条目</span>
        </a-menu-item>
        <a-menu-item key="MyKnowledge" v-if="hasRole(['employee', 'supervisor'])">
          <template #icon>
            <FileTextOutlined />
          </template>
          <span>我的提交</span>
        </a-menu-item>
        <a-menu-item key="Reading" v-if="hasRole(['admin', 'employee', 'supervisor'])">
          <template #icon>
            <ReadOutlined />
          </template>
          <span>阅读确认</span>
        </a-menu-item>
        <a-menu-item key="Review" v-if="hasRole(['supervisor'])">
          <template #icon>
            <AuditOutlined />
          </template>
          <span>到期复核</span>
        </a-menu-item>
        <a-menu-item key="Categories" v-if="hasRole(['admin'])">
          <template #icon>
            <FolderOutlined />
          </template>
          <span>制度目录</span>
        </a-menu-item>
        <a-menu-item key="Groups" v-if="hasRole(['admin'])">
          <template #icon>
            <TeamOutlined />
          </template>
          <span>责任小组</span>
        </a-menu-item>
      </a-menu>
    </a-layout-sider>
    <a-layout>
      <a-layout-header class="header">
        <div class="header-left">
          <a-button
            type="text"
            @click="collapsed = !collapsed"
            class="trigger"
          >
            <component :is="collapsed ? MenuUnfoldOutlined : MenuFoldOutlined" />
          </a-button>
          <span class="page-title">{{ pageTitle }}</span>
        </div>
        <div class="header-right">
          <a-dropdown>
            <a-space class="user-info">
              <UserOutlined />
              <span>{{ userStore.userName }}</span>
              <a-tag :color="roleColor">{{ roleLabel }}</a-tag>
            </a-space>
            <template #overlay>
              <a-menu @click="handleUserMenuClick">
                <a-menu-item key="profile">
                  <UserOutlined /> 个人信息
                </a-menu-item>
                <a-menu-divider />
                <a-menu-item key="logout">
                  <LogoutOutlined /> 退出登录
                </a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>
        </div>
      </a-layout-header>
      <a-layout-content class="content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </a-layout-content>
    </a-layout>
  </a-layout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  BookOutlined,
  HomeOutlined,
  BookOutlined as BookOutlined2,
  FileTextOutlined,
  ReadOutlined,
  AuditOutlined,
  FolderOutlined,
  TeamOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  UserOutlined,
  LogoutOutlined
} from '@ant-design/icons-vue'
import { useUserStore } from '@/stores/user'
import { Modal } from 'ant-design-vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const collapsed = ref(false)
const selectedKey = ref(route.name as string)

const hasRole = (roles: string[]) => {
  if (!userStore.user) return false
  return roles.includes(userStore.user.role)
}

const pageTitle = computed(() => {
  return route.meta.title as string || '首页'
})

const roleLabel = computed(() => {
  const labels: Record<string, string> = {
    admin: '管理员',
    employee: '员工',
    supervisor: '主管'
  }
  return labels[userStore.userRole || ''] || ''
})

const roleColor = computed(() => {
  const colors: Record<string, string> = {
    admin: 'red',
    employee: 'blue',
    supervisor: 'green'
  }
  return colors[userStore.userRole || ''] || 'default'
})

const handleMenuClick = ({ key }: { key: string }) => {
  if (key !== selectedKey.value) {
    selectedKey.value = key
    router.push({ name: key })
  }
}

const handleUserMenuClick = ({ key }: { key: string }) => {
  if (key === 'logout') {
    Modal.confirm({
      title: '确认退出',
      content: '确定要退出登录吗？',
      okText: '确定',
      cancelText: '取消',
      onOk: () => {
        userStore.logout()
      }
    })
  } else if (key === 'profile') {
    Modal.info({
      title: '个人信息',
      content: `用户名: ${userStore.user?.username}\n姓名: ${userStore.user?.name}\n角色: ${roleLabel.value}`
    })
  }
}

onMounted(() => {
  selectedKey.value = route.name as string
})
</script>

<style scoped>
.sider {
  position: fixed;
  height: 100vh;
  left: 0;
  top: 0;
  bottom: 0;
  z-index: 100;
}

.logo {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.logo-icon {
  font-size: 24px;
}

.header {
  background: #fff;
  padding: 0 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  position: fixed;
  top: 0;
  right: 0;
  left: 240px;
  z-index: 99;
  transition: left 0.2s;
}

.sider.collapsed + .ant-layout .header {
  left: 80px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.trigger {
  font-size: 18px;
  padding: 0 12px;
  height: 64px;
  border-radius: 0;
}

.page-title {
  font-size: 16px;
  font-weight: 500;
  color: #333;
}

.header-right {
  display: flex;
  align-items: center;
}

.user-info {
  cursor: pointer;
  padding: 8px 12px;
  border-radius: 4px;
  transition: background 0.2s;
}

.user-info:hover {
  background: #f5f5f5;
}

.content {
  margin-top: 64px;
  margin-left: 240px;
  padding: 24px;
  background: #f0f2f5;
  min-height: calc(100vh - 64px);
  transition: margin-left 0.2s;
}

.sider.collapsed + .ant-layout .content {
  margin-left: 80px;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

:deep(.ant-layout-sider-collapsed) {
  width: 80px !important;
  flex: 0 0 80px !important;
  max-width: 80px !important;
  min-width: 80px !important;
}

:deep(.ant-layout-sider-collapsed + .ant-layout .header) {
  left: 80px !important;
}

:deep(.ant-layout-sider-collapsed + .ant-layout .content) {
  margin-left: 80px !important;
}
</style>
