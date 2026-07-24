import { describe, it, expect, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import ReadingStatus from '@/pages/ReadingStatus.vue'
import { mockRequest, mockMessage } from '@/test/setup'

function mountPage() {
  const pinia = createPinia()
  setActivePinia(pinia)
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [{ path: '/', component: { template: '<div/>' } }],
  })
  const wrapper = mount(ReadingStatus, {
    global: {
      plugins: [pinia, router],
    },
  })
  return { wrapper }
}

function statusResponse(items: any[] = [], total = items.length) {
  return {
    code: 200,
    data: { items, total, page: 1, page_size: 10 },
  }
}

describe('ReadingStatus page', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    mockRequest.get.mockReset()
    mockRequest.post.mockReset()
    mockRequest.delete.mockReset()
  })

  it('loads reading status on mount with default params', async () => {
    mockRequest.get.mockResolvedValue(statusResponse([]))
    const { wrapper } = mountPage()
    await flushPromises()
    expect(mockRequest.get).toHaveBeenCalledWith('/reading/my-status', {
      params: { page: 1, page_size: 10, review_expiry_status: undefined },
    })
    wrapper.unmount()
  })

  it('updates stats totals from response', async () => {
    mockRequest.get.mockResolvedValue(
      statusResponse([
        { id: 1, is_read: true, knowledge_title: 'a' },
        { id: 2, is_read: false, knowledge_title: 'b' },
        { id: 3, is_read: true, knowledge_title: 'c' },
      ], 3)
    )
    const { wrapper } = mountPage()
    await flushPromises()
    const vm = wrapper.vm as any
    expect(vm.stats.total).toBe(3)
    expect(vm.stats.read).toBe(2)
    expect(vm.stats.unread).toBe(1)
    wrapper.unmount()
  })

  it('passes expiry filter when changed and reloads', async () => {
    mockRequest.get.mockResolvedValue(statusResponse([]))
    const { wrapper } = mountPage()
    await flushPromises()
    const vm = wrapper.vm as any

    vm.expiryFilter = 'upcoming'
    await vm.loadData()

    const calls = mockRequest.get.mock.calls.filter(
      (c: any[]) => c[1]?.params?.review_expiry_status === 'upcoming'
    )
    expect(calls.length).toBeGreaterThan(0)
    expect(calls[calls.length - 1][1].params).toMatchObject({
      review_expiry_status: 'upcoming',
    })
    wrapper.unmount()
  })

  it('mark as read calls API and reloads', async () => {
    mockRequest.get.mockResolvedValue(statusResponse([]))
    mockRequest.post.mockResolvedValue({ code: 200, data: null })
    const { wrapper } = mountPage()
    await flushPromises()
    const vm = wrapper.vm as any

    await vm.handleMarkRead(22)
    expect(mockRequest.post).toHaveBeenCalledWith('/reading/22')
    expect(mockMessage.success).toHaveBeenCalled()
    wrapper.unmount()
  })

  it('mark as unread calls delete API and reloads', async () => {
    mockRequest.get.mockResolvedValue(statusResponse([]))
    mockRequest.delete.mockResolvedValue({ code: 200, data: null })
    const { wrapper } = mountPage()
    await flushPromises()
    const vm = wrapper.vm as any

    await vm.handleMarkUnread(22)
    expect(mockRequest.delete).toHaveBeenCalledWith('/reading/22')
    expect(mockMessage.success).toHaveBeenCalled()
    wrapper.unmount()
  })

  it('viewDetail handles api failure with error message', async () => {
    mockRequest.get.mockResolvedValue(statusResponse([]))
    const { wrapper } = mountPage()
    await flushPromises()
    const vm = wrapper.vm as any

    // simulate getKnowledgeDetail failure by overriding the resolved value for next get
    mockRequest.get.mockRejectedValueOnce(new Error('network'))
    await vm.viewDetail({ knowledge_id: 1, is_read: false })
    await flushPromises()
    expect(mockMessage.error).toHaveBeenCalledWith('获取详情失败')
    wrapper.unmount()
  })

  it('pagination change updates page and reloads', async () => {
    mockRequest.get.mockResolvedValue(statusResponse([]))
    const { wrapper } = mountPage()
    await flushPromises()
    const vm = wrapper.vm as any

    vm.handleTableChange({ current: 3, pageSize: 5 })
    expect(vm.pagination.current).toBe(3)
    expect(vm.pagination.pageSize).toBe(5)
    wrapper.unmount()
  })
})
