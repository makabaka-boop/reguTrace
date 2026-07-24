import request, { type ApiResponse } from './request'

export interface CategoryNode {
  id: number
  name: string
  code?: string
  parent_id?: number
  group_id?: number
  sort_order: number
  is_active: boolean
  level: number
  path: string
  created_at: string
  updated_at: string
  children?: CategoryNode[]
}

export interface CategoryCreate {
  name: string
  code?: string
  parent_id?: number
  group_id?: number
  sort_order?: number
}

export interface CategoryUpdate {
  name?: string
  code?: string
  group_id?: number
  sort_order?: number
  is_active?: boolean
}

export const getCategoryTree = (include_inactive = false) => {
  return request.get<any, ApiResponse<CategoryNode[]>>('/categories', {
    params: { include_inactive }
  })
}

export const getCategoryList = (group_id?: number) => {
  return request.get<any, ApiResponse<CategoryNode[]>>('/categories/list', {
    params: { group_id }
  })
}

export const getCategoryDetail = (id: number) => {
  return request.get<any, ApiResponse<CategoryNode>>(`/categories/${id}`)
}

export const createCategory = (data: CategoryCreate) => {
  return request.post<any, ApiResponse<CategoryNode>>('/categories', data)
}

export const updateCategory = (id: number, data: CategoryUpdate) => {
  return request.put<any, ApiResponse<CategoryNode>>(`/categories/${id}`, data)
}

export const deleteCategory = (id: number) => {
  return request.delete<any, ApiResponse>(`/categories/${id}`)
}

export const moveCategory = (id: number, target_parent_id: number) => {
  return request.post<any, ApiResponse<CategoryNode>>(`/categories/${id}/move`, {
    target_parent_id
  })
}

export const mergeCategory = (id: number, target_category_id: number) => {
  return request.post<any, ApiResponse>(`/categories/${id}/merge`, {
    target_category_id
  })
}

export const copyCategory = (id: number, target_group_id: number, target_parent_id?: number) => {
  return request.post<any, ApiResponse>(`/categories/${id}/copy`, {
    target_group_id,
    target_parent_id
  })
}

export const deactivateCategory = (id: number) => {
  return request.post<any, ApiResponse<CategoryNode>>(`/categories/${id}/deactivate`)
}
