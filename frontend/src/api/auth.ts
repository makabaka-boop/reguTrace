import request, { type ApiResponse } from './request'

export interface LoginParams {
  username: string
  password: string
  role: string
}

export interface UserInfo {
  id: number
  username: string
  role: string
  name: string
  token?: string
  created_at: string
}

export const login = (params: LoginParams) => {
  return request.post<any, ApiResponse<UserInfo>>('/auth/login', params)
}

export const logout = () => {
  return request.post<any, ApiResponse>('/auth/logout')
}

export const getCurrentUser = () => {
  return request.get<any, ApiResponse<UserInfo>>('/auth/me')
}
