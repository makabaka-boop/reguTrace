import request, { type ApiResponse } from './request'

export interface Group {
  id: number
  name: string
  description: string
  created_at: string
}

export interface GroupCreate {
  name: string
  description?: string
}

export interface GroupUpdate {
  name?: string
  description?: string
}

export function getGroups() {
  return request.get<any, ApiResponse<Group[]>>('/groups')
}

export function getGroup(id: number) {
  return request.get<any, ApiResponse<Group>>(`/groups/${id}`)
}

export function createGroup(data: GroupCreate) {
  return request.post<any, ApiResponse<Group>>('/groups', data)
}

export function updateGroup(id: number, data: GroupUpdate) {
  return request.put<any, ApiResponse<Group>>(`/groups/${id}`, data)
}

export function deleteGroup(id: number) {
  return request.delete<any, ApiResponse>(`/groups/${id}`)
}
