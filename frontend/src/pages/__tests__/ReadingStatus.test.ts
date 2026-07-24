/**
 * 阅读确认页关键方法测试：
 * - loadData 的分页/到期筛选参数组装
 * - 统计（已确认/未确认）派生计算
 * - 标记已读/未读的状态更新与提示
 * - viewDetail 异常提示处理
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'

const getMyReadingStatus = vi.fn()
const markAsRead = vi.fn()
const markAsUnread = vi.fn()
vi.mock('@/api/reading', () => ({
  getMyReadingStatus: (...a: any[]) => getMyReadingStatus(...a),
  markAsRead: (...a: any[]) => markAsRead(...a),
  markAsUnread: (...a: any[]) => markAsUnread(...a),
}))

const getKnowledgeDetail = vi.fn()
vi.mock('@/api/knowledge', () => ({
  getKnowledgeDetail: (...a: any[]) => getKnowledgeDetail(...a),
}))

import ReadingStatus from '@/pages/ReadingStatus.vue'
import { message } from 'ant-design-vue'

const stubAll = new Proxy(
  {},
  {
    get: () => ({ template: '<div><slot /></div>' }),
    has: () => true,
  }
)

async function mountPage(items: any[] = []) {
  getMyReadingStatus.mockResolvedValue({
    code: 200,
    data: { items, total: items.length, page: 1, page_size: 10 },
  })
  const wrapper = mount(ReadingStatus, {
    global: { stubs: stubAll as any, renderStubDefaultSlot: true },
  })
  await flushPromises()
  return wrapper
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('ReadingStatus - loadData', () => {
  it('组装分页与到期筛选参数', async () => {
    const wrapper = await mountPage()
    wrapper.vm.expiryFilter = 'upcoming'
    getMyReadingStatus.mockClear()
    await wrapper.vm.loadData()
    expect(getMyReadingStatus).toHaveBeenCalledWith(
      expect.objectContaining({ page: 1, page_size: 10, review_expiry_status: 'upcoming' })
    )
  })

  it('加载后派生 已确认/未确认 统计', async () => {
    const wrapper = await mountPage([
      { id: 1, knowledge_id: 11, is_read: true },
      { id: 2, knowledge_id: 12, is_read: false },
      { id: 3, knowledge_id: 13, is_read: true },
    ])
    expect(wrapper.vm.stats.total).toBe(3)
    expect(wrapper.vm.stats.read).toBe(2)
    expect(wrapper.vm.stats.unread).toBe(1)
  })
})

describe('ReadingStatus - 标记状态', () => {
  it('handleMarkRead 成功提示并刷新', async () => {
    const wrapper = await mountPage()
    markAsRead.mockResolvedValue({ code: 200 })
    getMyReadingStatus.mockClear()
    await wrapper.vm.handleMarkRead(11)
    expect(markAsRead).toHaveBeenCalledWith(11)
    expect(message.success).toHaveBeenCalledWith('已标记为已读')
    expect(getMyReadingStatus).toHaveBeenCalled()
  })

  it('handleMarkUnread 成功提示', async () => {
    const wrapper = await mountPage()
    markAsUnread.mockResolvedValue({ code: 200 })
    await wrapper.vm.handleMarkUnread(12)
    expect(markAsUnread).toHaveBeenCalledWith(12)
    expect(message.success).toHaveBeenCalledWith('已标记为未读')
  })
})

describe('ReadingStatus - viewDetail', () => {
  it('成功获取详情后打开弹窗', async () => {
    const wrapper = await mountPage()
    getKnowledgeDetail.mockResolvedValue({ code: 200, data: { id: 11, title: 'X', is_read: true } })
    await wrapper.vm.viewDetail({ knowledge_id: 11, is_read: true })
    expect(wrapper.vm.detailModalVisible).toBe(true)
    expect(wrapper.vm.currentDetail?.title).toBe('X')
  })

  it('未读条目查看详情时自动标记已读', async () => {
    const wrapper = await mountPage()
    getKnowledgeDetail.mockResolvedValue({ code: 200, data: { id: 11, title: 'X' } })
    markAsRead.mockResolvedValue({ code: 200 })
    await wrapper.vm.viewDetail({ knowledge_id: 11, is_read: false })
    expect(markAsRead).toHaveBeenCalledWith(11)
  })

  it('接口异常时提示获取详情失败', async () => {
    const wrapper = await mountPage()
    getKnowledgeDetail.mockRejectedValue(new Error('boom'))
    await wrapper.vm.viewDetail({ knowledge_id: 99, is_read: true })
    expect(message.error).toHaveBeenCalledWith('获取详情失败')
  })
})

describe('ReadingStatus - 分页', () => {
  it('handleTableChange 更新分页并重新加载', async () => {
    const wrapper = await mountPage()
    getMyReadingStatus.mockClear()
    await wrapper.vm.handleTableChange({ current: 2, pageSize: 20 })
    expect(wrapper.vm.pagination.current).toBe(2)
    expect(wrapper.vm.pagination.pageSize).toBe(20)
    expect(getMyReadingStatus).toHaveBeenCalled()
  })
})
