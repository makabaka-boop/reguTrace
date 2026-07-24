import request from './request'

export interface KnowledgeItem {
  id: number
  title: string
  content: string
  category_id: number
  category_name?: string
  submitter_id: number
  submitter_name?: string
  review_status: 'pending' | 'approved' | 'rejected'
  reject_reason?: string
  is_read?: boolean
  created_at: string
  updated_at: string
}

export interface KnowledgeListResponse {
  items: KnowledgeItem[]
  total: number
  page: number
  page_size: number
}

export interface KnowledgeCreate {
  title: string
  content: string
  category_id: number
}

export interface KnowledgeUpdate {
  title?: string
  content?: string
  category_id?: number
}

export const getKnowledgeList = (params: {
  category_id?: number
  page?: number
  page_size?: number
  review_status?: string
}) => {
  return request.get<any, ApiResponse<KnowledgeListResponse>>('/knowledge', { params })
}

export const getMyKnowledge = (params: {
  page?: number
  page_size?: number
}) => {
  return request.get<any, ApiResponse<KnowledgeListResponse>>('/knowledge/my', { params })
}

export const getKnowledgeDetail = (id: number) => {
  return request.get<any, ApiResponse<KnowledgeItem>>(`/knowledge/${id}`)
}

export const createKnowledge = (data: KnowledgeCreate) => {
  return request.post<any, ApiResponse<KnowledgeItem>>('/knowledge', data)
}

export const updateKnowledge = (id: number, data: KnowledgeUpdate) => {
  return request.put<any, ApiResponse<KnowledgeItem>>(`/knowledge/${id}`, data)
}

export const deleteKnowledge = (id: number) => {
  return request.delete<any, ApiResponse>(`/knowledge/${id}`)
}
