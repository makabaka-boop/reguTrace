/**
 * 接口封装测试：验证各 api 方法的请求方法、URL 与参数组装是否正确。
 * 通过 mock `@/api/request` 的默认导出，拦截真实 axios 调用。
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

// 使用可断言的 spy 替代真实 request 实例。
// vi.hoisted 保证这些变量在被提升的 vi.mock 工厂内可安全引用。
const { get, post, put, del } = vi.hoisted(() => ({
  get: vi.fn(() => Promise.resolve({ code: 200, data: {} })),
  post: vi.fn(() => Promise.resolve({ code: 200, data: {} })),
  put: vi.fn(() => Promise.resolve({ code: 200, data: {} })),
  del: vi.fn(() => Promise.resolve({ code: 200, data: {} })),
}))

vi.mock('@/api/request', () => ({
  default: { get, post, put, delete: del },
}))

import * as authApi from '@/api/auth'
import * as knowledgeApi from '@/api/knowledge'
import * as readingApi from '@/api/reading'
import * as categoryApi from '@/api/category'
import * as reviewApi from '@/api/review'

beforeEach(() => {
  vi.clearAllMocks()
})

describe('auth api', () => {
  it('login 使用 POST /auth/login 并透传参数', () => {
    const params = { username: 'u', password: 'p', role: 'employee' }
    authApi.login(params)
    expect(post).toHaveBeenCalledWith('/auth/login', params)
  })

  it('getCurrentUser 使用 GET /auth/me', () => {
    authApi.getCurrentUser()
    expect(get).toHaveBeenCalledWith('/auth/me')
  })
})

describe('knowledge api', () => {
  it('getKnowledgeList 组装 params', () => {
    const params = { category_id: 1, page: 2, page_size: 10, review_status: 'pending' }
    knowledgeApi.getKnowledgeList(params)
    expect(get).toHaveBeenCalledWith('/knowledge', { params })
  })

  it('getKnowledgeDetail 拼接 id 到路径', () => {
    knowledgeApi.getKnowledgeDetail(42)
    expect(get).toHaveBeenCalledWith('/knowledge/42')
  })

  it('createKnowledge 使用 POST 透传数据', () => {
    const data = { title: 't', content: 'c', category_id: 1 }
    knowledgeApi.createKnowledge(data)
    expect(post).toHaveBeenCalledWith('/knowledge', data)
  })

  it('updateKnowledge 使用 PUT 并拼接 id', () => {
    knowledgeApi.updateKnowledge(5, { title: 'x' })
    expect(put).toHaveBeenCalledWith('/knowledge/5', { title: 'x' })
  })

  it('deleteKnowledge 使用 DELETE 并拼接 id', () => {
    knowledgeApi.deleteKnowledge(7)
    expect(del).toHaveBeenCalledWith('/knowledge/7')
  })
})

describe('reading api', () => {
  it('markAsRead 使用 POST /reading/:id', () => {
    readingApi.markAsRead(3)
    expect(post).toHaveBeenCalledWith('/reading/3')
  })

  it('markAsUnread 使用 DELETE /reading/:id', () => {
    readingApi.markAsUnread(3)
    expect(del).toHaveBeenCalledWith('/reading/3')
  })

  it('getMyReadingStatus 组装分页参数', () => {
    readingApi.getMyReadingStatus({ page: 1, page_size: 20 })
    expect(get).toHaveBeenCalledWith('/reading/my-status', { params: { page: 1, page_size: 20 } })
  })
})

describe('category api', () => {
  it('getCategoryTree 默认 include_inactive=false', () => {
    categoryApi.getCategoryTree()
    expect(get).toHaveBeenCalledWith('/categories', { params: { include_inactive: false } })
  })

  it('createCategory 使用 POST', () => {
    const data = { name: 'n' }
    categoryApi.createCategory(data)
    expect(post).toHaveBeenCalledWith('/categories', data)
  })

  it('moveCategory 使用 POST /:id/move 并携带目标父节点', () => {
    categoryApi.moveCategory(1, 2)
    expect(post).toHaveBeenCalledWith('/categories/1/move', { target_parent_id: 2 })
  })

  it('copyCategory 携带目标小组与父节点', () => {
    categoryApi.copyCategory(1, 9, 3)
    expect(post).toHaveBeenCalledWith('/categories/1/copy', { target_group_id: 9, target_parent_id: 3 })
  })
})

describe('review api', () => {
  it('approveKnowledge 默认空对象 body', () => {
    reviewApi.approveKnowledge(1)
    expect(post).toHaveBeenCalledWith('/review/1/approve', {})
  })

  it('rejectKnowledge 透传备注', () => {
    reviewApi.rejectKnowledge(1, { remark: '不合规' })
    expect(post).toHaveBeenCalledWith('/review/1/reject', { remark: '不合规' })
  })

  it('batchApprove 透传 ids', () => {
    reviewApi.batchApprove({ knowledge_ids: [1, 2] })
    expect(post).toHaveBeenCalledWith('/review/batch-approve', { knowledge_ids: [1, 2] })
  })
})
