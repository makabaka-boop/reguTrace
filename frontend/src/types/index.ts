export type UserRole = 'admin' | 'employee' | 'supervisor'

export interface User {
  id: number
  username: string
  role: UserRole
  name: string
  created_at: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  user: User
}

export interface CategoryTreeData {
  key: string | number
  title: string
  children?: CategoryTreeData[]
  isLeaf?: boolean
  disabled?: boolean
  data?: any
  slots?: {
    icon?: string
    title?: string
  }
}
