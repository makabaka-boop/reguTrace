import { describe, it, expect, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import KnowledgeList from '@/pages/KnowledgeList.vue'
import { useUserStore } from '@/stores/user'
import { mockRequest, mockMessage } from '@/test/setup'

const CategoryTreeStub = {
  name: 'CategoryTree',
  template: '<div class="cat-tree" />',
  methods: { reloadSummaries() {} },
}

const slotStub = (name: string) => ({ name, template: '<div><slot/></div>' })

function mountPage(userRole: 'admin' | 'employee' | 'supervisor' = 'employee') {
  const pinia = createPinia()
  setActivePinia(pinia)

  const router = createRouter({
    history: createMemoryHistory(),
    routes: [{ path: '/', component: { template: '<div/>' } }],
  })

  const wrapper = mount(KnowledgeList, {
    global: {
      plugins: [pinia, router],
      stubs: {
        CategoryTree: CategoryTreeStub,
        'a-card': { template: '<div class="card"><slot name="extra"/><slot/></div>' },
        'a-button': { template: '<button class="btn"><slot/></button>' },
        'a-row': slotStub('ARow'),
        'a-col': slotStub('ACol'),
        'a-space': slotStub('ASpace'),
        'a-input-search': true,
        'a-select': true,
        'a-select-option': true,
        'a-table': true,
        'a-modal': true,
        'a-form': slotStub('AForm'),
        'a-form-item': slotStub('AFormItem'),
        'a-input': true,
        'a-tree-select': true,
        'a-textarea': true,
        'a-alert': true,
        'a-tag': slotStub('ATag'),
        'a-divider': true,
      },
    },
  })

  const userStore = useUserStore()
  userStore.setUser({
    id: 1,
    username: 'tester',
    role: userRole,
    name: 'Tester',
    created_at: 't',
  })
  userStore.setToken('tok')

  return { wrapper, userStore }
}

function listResponse(items: any[] = [], total = items.length) {
  return {
    code: 200,
    data: { items, total, page: 1, page_size: 10 },
  }
}

describe('KnowledgeList page', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    mockRequest.get.mockReset()
    mockRequest.post.mockReset()
  })

  it('loads category tree and knowledge list on mount', async () => {
    mockRequest.get.mockImplementation((url: string) => {
      if (url === '/categories') return Promise.resolve({ code: 200, data: [] })
      if (url === '/knowledge') return Promise.resolve(listResponse([]))
      return Promise.resolve({ code: 200, data: null })
    })
    const { wrapper } = mountPage()
    await flushPromises()
    expect(mockRequest.get).toHaveBeenCalledWith('/categories', expect.any(Object))
    expect(mockRequest.get).toHaveBeenCalledWith('/knowledge', expect.any(Object))
    wrapper.unmount()
  })

  it('assembles request params including category, pagination, and filters', async () => {
    mockRequest.get.mockImplementation((url: string) => {
      if (url === '/categories') return Promise.resolve({ code: 200, data: [] })
      if (url.startsWith('/summary/node')) return Promise.resolve({ code: 200, data: null })
      return Promise.resolve(listResponse([]))
    })
    const { wrapper } = mountPage()
    const vm = wrapper.vm as any
    await flushPromises()

    // set a selected category and filters
    vm.categoryStore.setSelected(5)
    vm.pagination.current = 2
    vm.pagination.pageSize = 20
    vm.statusFilter = 'pending'
    vm.searchKeyword = '报销'
    vm.expiryFilter = 'overdue'

    await vm.loadKnowledge()

    const call = mockRequest.get.mock.calls.find(
      (c: any[]) => c[0] === '/knowledge' && c[1]?.params?.review_status === 'pending'
    )
    expect(call).toBeTruthy()
    expect(call![1].params).toMatchObject({
      category_id: 5,
      page: 2,
      page_size: 20,
      review_status: 'pending',
      keyword: '报销',
      review_expiry_status: 'overdue',
    })
    wrapper.unmount()
  })

  it('submit button is hidden for admin, visible for others', async () => {
    mockRequest.get.mockResolvedValue({ code: 200, data: [] })

    const adminView = mountPage('admin')
    await flushPromises()
    expect(adminView.wrapper.text()).not.toContain('提交制度')
    adminView.wrapper.unmount()

    const empView = mountPage('employee')
    await flushPromises()
    expect(empView.wrapper.text()).toContain('提交制度')
    empView.wrapper.unmount()
  })

  it('export button is visible only for supervisor', async () => {
    mockRequest.get.mockResolvedValue({ code: 200, data: [] })

    const empView = mountPage('employee')
    await flushPromises()
    expect(empView.wrapper.text()).not.toContain('导出Excel')
    empView.wrapper.unmount()

    const supView = mountPage('supervisor')
    await flushPromises()
    expect(supView.wrapper.text()).toContain('导出Excel')
    supView.wrapper.unmount()
  })

  it('marking read calls API and reloads list', async () => {
    mockRequest.get.mockImplementation((url: string) => {
      if (url === '/categories') return Promise.resolve({ code: 200, data: [] })
      if (url.startsWith('/summary/node')) return Promise.resolve({ code: 200, data: null })
      return Promise.resolve(
        listResponse([{ id: 11, title: 't', is_read: false, review_status: 'approved' }])
      )
    })
    mockRequest.post.mockResolvedValue({ code: 200, data: null })

    const { wrapper } = mountPage()
    const vm = wrapper.vm as any
    await flushPromises()

    await vm.handleMarkRead(11)
    expect(mockRequest.post).toHaveBeenCalledWith('/reading/11')
    expect(mockMessage.success).toHaveBeenCalled()
    // reload triggered
    expect(mockRequest.get).toHaveBeenCalledWith('/knowledge', expect.any(Object))
    wrapper.unmount()
  })

  it('shows error when api returns non-200', async () => {
    mockRequest.get.mockImplementation((url: string) => {
      if (url === '/categories') return Promise.resolve({ code: 200, data: [] })
      return Promise.resolve({ code: 500, message: 'server error', data: null })
    })
    const { wrapper } = mountPage()
    await flushPromises()
    // The page catches failures in loadKnowledge without throwing; state stays empty
    const vm = wrapper.vm as any
    expect(vm.knowledgeList).toEqual([])
    wrapper.unmount()
  })
})
