import request from './request'

export interface ReadingStatusItem {
  id: number
  knowledge_id: number
  knowledge_title?: string
  user_id: number
  is_read: boolean
  read_at: string
}

export const markAsRead = (knowledge_id: number) => {
  return request.post<any, ApiResponse>(`/reading/${knowledge_id}`)
}

export const markAsUnread = (knowledge_id: number) => {
  return request.delete<any, ApiResponse>(`/reading/${knowledge_id}`)
}

export const getMyReadingStatus = (params: {
  page?: number
  page_size?: number
}) => {
  return request.get<any, ApiResponse<{
    items: ReadingStatusItem[]
    total: number
    page: number
    page_size: number
  }>>('/reading/my-status', { params })
}
