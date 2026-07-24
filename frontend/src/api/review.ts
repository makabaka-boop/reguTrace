import request from './request'
import type { KnowledgeItem, KnowledgeListResponse } from './knowledge'

export interface ReviewRequest {
  remark?: string
  new_category_id?: number
}

export interface ReviewBatchRequest {
  knowledge_ids: number[]
  remark?: string
}

export const getPendingList = (params: {
  page?: number
  page_size?: number
}) => {
  return request.get<any, ApiResponse<KnowledgeListResponse>>('/review/pending', { params })
}

export const getStatistics = () => {
  return request.get<any, ApiResponse<{
    pending_count: number
    approved_count: number
    rejected_count: number
  }>>('/review/statistics')
}

export const approveKnowledge = (id: number, data: ReviewRequest = {}) => {
  return request.post<any, ApiResponse<KnowledgeItem>>(`/review/${id}/approve`, data)
}

export const rejectKnowledge = (id: number, data: ReviewRequest = {}) => {
  return request.post<any, ApiResponse<KnowledgeItem>>(`/review/${id}/reject`, data)
}

export const batchApprove = (data: ReviewBatchRequest) => {
  return request.post<any, ApiResponse>('/review/batch-approve', data)
}

export const batchReject = (data: ReviewBatchRequest) => {
  return request.post<any, ApiResponse>('/review/batch-reject', data)
}
