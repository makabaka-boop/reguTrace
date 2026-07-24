import request, { type ApiResponse } from './request'

export interface NodeSummary {
  category_id: number
  total_count: number
  unread_count: number
  pending_count: number
  updated_at?: string
}

export const getNodeSummary = (node_id: number) => {
  return request.get<any, ApiResponse<NodeSummary>>(`/summary/node/${node_id}`)
}

export const getAllNodesSummary = () => {
  return request.get<any, ApiResponse<NodeSummary[]>>('/summary/all-nodes')
}

export const rebuildSummaries = () => {
  return request.post<any, ApiResponse>('/summary/rebuild')
}
