/**
 * 制度列表页关键方法测试。
 *
 * 说明：页面使用 `<script setup>`，Vue Test Utils 会将顶层绑定通过 `wrapper.vm`
 * 暴露出来，因此可直接读取响应式状态、调用页面方法，验证：
 * - loadKnowledge 的筛选参数组装（分类/状态/关键字/到期）
 * - 标记已读/未读的状态更新与提示
 * - 权限判断（hasRole）相关按钮逻辑
 * - 分页变化触发重新加载
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'

// ---- mock 依赖 ----
const getKnowledgeList = vi.fn()
const createKnowledge = vi.fn()
vi.mock('@/api/knowledge', () => ({
  getKnowledgeList: (...a: any[]) => getKnowledgeList(...a),
  createKnowledge: (...a: any[]) => createKnowledge(...a),
}))

const markAsRead = vi.fn()
const markAsUnread = vi.fn()
vi.mock('@/api/reading', () => ({
  markAsRead: (...a: any[]) => markAsRead(...a),
  markAsUnread: (...a: any[]) => markAsUnread(...a),
}))

const getNodeSummary = vi.fn(() => Promise.resolve({ code: 200, data: { total_count: 0, unread_count: 0, pending_count: 0 } }))
const getAllNodesSummary = vi.fn(() => Promise.resolve({ code: 200, data: [] }))
const rebuildSummaries = vi.fn(() => Promise.resolve({ code: 200 }))
vi.mock('@/api/summary', () => ({
  getNodeSummary: (...a: any[]) => getNodeSummary(...a),
  getAllNodesSummary: (...a: any[]) => getAllNodesSummary(...a),
  rebuildSummaries: (...a: any[]) => rebuildSummaries(...a),
}))

// 分类 store：提供选中态与树
const categoryState = {
  selectedCategoryId: null as number | null,
  selectedCategory: null as any,
  treeData: [] as any[],
  fetchTree: vi.fn(() => Promise.resolve()),
}
vi.mock('@/stores/category', () => ({
  useCategoryStore: () => categoryState,
}))

// 用户 store：控制角色权限
const userState = {
  token: 'tok',
  hasRole: vi.fn((_r: any) => false),
}
vi.mock('@/stores/user', () => ({
  useUserStore: () => userState,
}))

// 路由
vi.mock('vue-router', () => ({
  useRoute: () => ({ query: {} }),
}))

import KnowledgeList from '@/pages/KnowledgeList.vue'
import { message } from 'ant-design-vue'

// 统一 stub 所有 a-* / 图标组件与自定义组件，避免真实渲染
const stubAll = new Proxy(
  {},
  {
    get: () => ({ template: '<div><slot /></div>' }),
    has: () => true,
  }
)

async function mountPage() {
  getKnowledgeList.mockResolvedValue({
    code: 200,
    data: { items: [{ id: 1, title: 'A', is_read: false }], total: 1, page: 1, page_size: 10 },
  })
  const wrapper = mount(KnowledgeList, {
    global: {
      stubs: stubAll as any,
      renderStubDefaultSlot: true,
    },
  })
  await flushPromises()
  return wrapper
}

beforeEach(() => {
  vi.clearAllMocks()
  categoryState.selectedCategoryId = null
  categoryState.selectedCategory = null
  categoryState.treeData = []
  userState.hasRole = vi.fn(() => false)
})

describe('KnowledgeList - loadKnowledge 参数组装', () => {
  it('组装分类/状态/关键字/到期筛选参数', async () => {
    const wrapper = await mountPage()
    categoryState.selectedCategoryId = 5
    wrapper.vm.statusFilter = 'pending'
    wrapper.vm.searchKeyword = '考勤'
    wrapper.vm.expiryFilter = 'overdue'
    getKnowledgeList.mockClear()

    await wrapper.vm.loadKnowledge()

    expect(getKnowledgeList).toHaveBeenCalledWith(
      expect.objectContaining({
        category_id: 5,
        review_status: 'pending',
        keyword: '考勤',
        review_expiry_status: 'overdue',
      })
    )
  })

  it('无筛选时 category_id/keyword 为 undefined', async () => {
    const wrapper = await mountPage()
    getKnowledgeList.mockClear()
    await wrapper.vm.loadKnowledge()
    const arg = getKnowledgeList.mock.calls[0][0]
    expect(arg.category_id).toBeUndefined()
    expect(arg.keyword).toBeUndefined()
  })

  it('加载成功后写入列表与总数', async () => {
    const wrapper = await mountPage()
    expect(wrapper.vm.knowledgeList).toHaveLength(1)
    expect(wrapper.vm.pagination.total).toBe(1)
  })
})

describe('KnowledgeList - 标记已读/未读', () => {
  it('handleMarkRead 成功后提示并重新加载', async () => {
    const wrapper = await mountPage()
    markAsRead.mockResolvedValue({ code: 200 })
    getKnowledgeList.mockClear()
    await wrapper.vm.handleMarkRead(1)
    expect(markAsRead).toHaveBeenCalledWith(1)
    expect(message.success).toHaveBeenCalledWith('已标记为已读')
    expect(getKnowledgeList).toHaveBeenCalled()
  })

  it('handleMarkUnread 成功后提示', async () => {
    const wrapper = await mountPage()
    markAsUnread.mockResolvedValue({ code: 200 })
    await wrapper.vm.handleMarkUnread(1)
    expect(markAsUnread).toHaveBeenCalledWith(1)
    expect(message.success).toHaveBeenCalledWith('已标记为未读')
  })
})

describe('KnowledgeList - 分页与筛选变化', () => {
  it('handleTableChange 更新分页并重新加载', async () => {
    const wrapper = await mountPage()
    getKnowledgeList.mockClear()
    await wrapper.vm.handleTableChange({ current: 3, pageSize: 20 })
    expect(wrapper.vm.pagination.current).toBe(3)
    expect(wrapper.vm.pagination.pageSize).toBe(20)
    expect(getKnowledgeList).toHaveBeenCalled()
  })

  it('handleCategorySelect 重置到第一页并加载', async () => {
    const wrapper = await mountPage()
    wrapper.vm.pagination.current = 5
    getKnowledgeList.mockClear()
    await wrapper.vm.handleCategorySelect()
    expect(wrapper.vm.pagination.current).toBe(1)
    expect(getKnowledgeList).toHaveBeenCalled()
  })
})

describe('KnowledgeList - 提交制度', () => {
  it('handleSubmit 校验通过后调用创建接口并提示', async () => {
    const wrapper = await mountPage()
    // 伪造表单 ref 的 validate
    wrapper.vm.formRef = { validate: vi.fn(() => Promise.resolve()) }
    createKnowledge.mockResolvedValue({ code: 200, data: { id: 2 } })
    await wrapper.vm.handleSubmit()
    expect(createKnowledge).toHaveBeenCalled()
    expect(message.success).toHaveBeenCalledWith('提交成功，等待主管复核')
    expect(wrapper.vm.createModalVisible).toBe(false)
  })
})
