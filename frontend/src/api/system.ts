import request from '@/utils/request'
import type { AxiosResponse } from 'axios'

// ═══════════════════════════════════════════════════════════════
// 通用类型
// ═══════════════════════════════════════════════════════════════

export interface PageResult<T> {
  items: T[]
  total: number
  page: number
  size: number
  pages: number
}

export interface PageQuery {
  keyword?: string
  page?: number
  size?: number
}

// ═══════════════════════════════════════════════════════════════
// 一、部门 Department
// ═══════════════════════════════════════════════════════════════

export interface Department {
  id: number
  name: string
  code: string
  parent_id: number | null
  sort_order: number
  is_active: boolean
  created_at: string
  updated_at: string
  created_by: string | null
  updated_by: string | null
}

export interface DeptQuery extends PageQuery {
  is_active?: boolean
}

export interface DeptCreate {
  name: string
  code: string
  parent_id?: number | null
  sort_order?: number
  is_active?: boolean
}

export interface DeptUpdate {
  name?: string
  code?: string
  parent_id?: number | null
  sort_order?: number
  is_active?: boolean
}

export const deptApi = {
  list: (params: DeptQuery): Promise<AxiosResponse<PageResult<Department>>> =>
    request.get('/system/departments', { params }),

  create: (data: DeptCreate): Promise<AxiosResponse<Department>> =>
    request.post('/system/departments', data),

  detail: (id: number): Promise<AxiosResponse<Department>> =>
    request.get(`/system/departments/${id}`),

  update: (id: number, data: DeptUpdate): Promise<AxiosResponse<Department>> =>
    request.put(`/system/departments/${id}`, data),

  remove: (id: number): Promise<AxiosResponse<void>> =>
    request.delete(`/system/departments/${id}`),
}

// ═══════════════════════════════════════════════════════════════
// 二、权限 Permission
// ═══════════════════════════════════════════════════════════════

export type PermissionAction = 'read' | 'write' | 'delete' | 'admin'

export interface Permission {
  id: number
  name: string
  code: string
  resource: string
  action: PermissionAction
  description: string | null
  parent_id: number | null
  created_at: string
  updated_at: string
}

export interface PermQuery extends PageQuery {
  action?: PermissionAction
}

export interface PermCreate {
  name: string
  code: string
  resource: string
  action: PermissionAction
  description?: string | null
  parent_id?: number | null
}

export type PermUpdate = Partial<PermCreate>

export const permApi = {
  list: (params: PermQuery): Promise<AxiosResponse<PageResult<Permission>>> =>
    request.get('/system/permissions', { params }),

  create: (data: PermCreate): Promise<AxiosResponse<Permission>> =>
    request.post('/system/permissions', data),

  detail: (id: number): Promise<AxiosResponse<Permission>> =>
    request.get(`/system/permissions/${id}`),

  update: (id: number, data: PermUpdate): Promise<AxiosResponse<Permission>> =>
    request.put(`/system/permissions/${id}`, data),

  remove: (id: number): Promise<AxiosResponse<void>> =>
    request.delete(`/system/permissions/${id}`),
}

// ═══════════════════════════════════════════════════════════════
// 三、角色 Role
// ═══════════════════════════════════════════════════════════════

export interface RoleBase {
  id: number
  name: string
  code: string
  description: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface RoleDetail extends RoleBase {
  permissions: Pick<Permission, 'id' | 'name' | 'code' | 'action'>[]
}

export interface RoleQuery extends PageQuery {
  is_active?: boolean
}

export interface RoleCreate {
  name: string
  code: string
  description?: string | null
  is_active?: boolean
  permission_ids?: number[]
}

export interface RoleUpdate {
  name?: string
  code?: string
  description?: string | null
  is_active?: boolean
  permission_ids?: number[]
}

export const roleApi = {
  list: (params: RoleQuery): Promise<AxiosResponse<PageResult<RoleBase>>> =>
    request.get('/system/roles', { params }),

  create: (data: RoleCreate): Promise<AxiosResponse<RoleDetail>> =>
    request.post('/system/roles', data),

  detail: (id: number): Promise<AxiosResponse<RoleDetail>> =>
    request.get(`/system/roles/${id}`),

  update: (id: number, data: RoleUpdate): Promise<AxiosResponse<RoleDetail>> =>
    request.put(`/system/roles/${id}`, data),

  remove: (id: number): Promise<AxiosResponse<void>> =>
    request.delete(`/system/roles/${id}`),
}

// ═══════════════════════════════════════════════════════════════
// 四、用户 User
// ═══════════════════════════════════════════════════════════════

export interface UserBase {
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
}

export interface UserDetail extends UserBase {
  department: Pick<Department, 'id' | 'name' | 'code'> | null
  roles: Pick<RoleBase, 'id' | 'name' | 'code' | 'is_active'>[]
}

export interface UserQuery extends PageQuery {
  is_active?: boolean
  department_id?: number
}

export interface UserCreate {
  username: string
  password: string
  real_name: string
  email?: string | null
  phone?: string | null
  is_active?: boolean
  department_id?: number | null
  role_ids?: number[]
}

export interface UserUpdate {
  real_name?: string
  email?: string | null
  phone?: string | null
  is_active?: boolean
  department_id?: number | null
  role_ids?: number[]
}

export interface ResetPasswordPayload {
  new_password: string
}

export interface ChangePasswordPayload {
  old_password: string
  new_password: string
  confirm_password: string
}

export const userApi = {
  list: (params: UserQuery): Promise<AxiosResponse<PageResult<UserBase>>> =>
    request.get('/system/users', { params }),

  create: (data: UserCreate): Promise<AxiosResponse<UserDetail>> =>
    request.post('/system/users', data),

  detail: (id: number): Promise<AxiosResponse<UserDetail>> =>
    request.get(`/system/users/${id}`),

  update: (id: number, data: UserUpdate): Promise<AxiosResponse<UserDetail>> =>
    request.put(`/system/users/${id}`, data),

  remove: (id: number): Promise<AxiosResponse<void>> =>
    request.delete(`/system/users/${id}`),

  resetPassword: (id: number, data: ResetPasswordPayload): Promise<AxiosResponse<void>> =>
    request.post(`/system/users/${id}/reset-password`, data),

  changePassword: (data: ChangePasswordPayload): Promise<AxiosResponse<void>> =>
    request.post('/system/me/change-password', data),
}

// ═══════════════════════════════════════════════════════════════
// 五、审计日志 AuditLog（只读）
// ═══════════════════════════════════════════════════════════════

export type AuditAction = string
export type AuditResourceType = string

export interface AuditLog {
  id: number
  user_id: number
  username: string
  action: AuditAction
  resource_type: AuditResourceType
  resource_id: string
  detail: Record<string, unknown> | null
  ip_address: string | null
  user_agent: string | null
  created_at: string
}

export interface AuditQuery {
  user_id?: number
  action?: AuditAction
  resource_type?: AuditResourceType
  start_time?: string
  end_time?: string
  page?: number
  size?: number
}

export const auditApi = {
  list: (params: AuditQuery): Promise<AxiosResponse<PageResult<AuditLog>>> =>
    request.get('/system/audit-logs', { params }),
}
