import request from '@/utils/request'
import type { AxiosResponse } from 'axios'

export interface LoginRequest {
  username: string
  password: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface RefreshTokenRequest {
  refresh_token: string
}

export interface ChangePasswordRequest {
  old_password: string
  new_password: string
  confirm_password: string
}

export interface UserRole {
  id: number
  name: string
  code: string
  is_active: boolean
}

export interface Department {
  id: number
  name: string
  code: string
}

export interface CurrentUser {
  id: number
  username: string
  real_name: string
  email: string | null
  phone: string | null
  is_active: boolean
  department_id: number | null
  created_at: string
  updated_at: string
  created_by: string | null
  updated_by: string | null
  department: Department | null
  roles: UserRole[]
  permission_scopes: string[]
}

export const authApi = {
  login: (data: LoginRequest): Promise<AxiosResponse<TokenResponse>> =>
    request.post('/auth/login', data),

  refresh: (data: RefreshTokenRequest): Promise<AxiosResponse<TokenResponse>> =>
    request.post('/auth/refresh', data),

  me: (): Promise<AxiosResponse<CurrentUser>> =>
    request.get('/auth/me'),

  changePassword: (data: ChangePasswordRequest): Promise<AxiosResponse<void>> =>
    request.post('/system/me/change-password', data),
}
