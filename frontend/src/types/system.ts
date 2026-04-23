/**
 * 系统管理模块类型定义
 */

import type { BaseEntity, ActivatableEntity, DescribableEntity, CodedEntity, PageQuery } from './common'

// ═══════════════════════════════════════════════════════════════
// 用户
// ═══════════════════════════════════════════════════════════════

export interface SysUser extends BaseEntity, ActivatableEntity {
  username: string
  real_name: string
  email: string | null
  phone: string | null
  department_id: number | null
  roles: SysRole[]
}

export interface SysUserQuery extends PageQuery {
  department_id?: number
  is_active?: boolean
}

export interface SysUserCreate {
  username: string
  password: string
  real_name: string
  email?: string | null
  phone?: string | null
  department_id?: number | null
  role_ids?: number[]
  is_active?: boolean
}

export interface SysUserUpdate {
  real_name?: string
  email?: string | null
  phone?: string | null
  department_id?: number | null
  role_ids?: number[]
  is_active?: boolean
}

// ═══════════════════════════════════════════════════════════════
// 角色
// ═══════════════════════════════════════════════════════════════

export interface SysRole extends BaseEntity, DescribableEntity, CodedEntity {
  is_system: boolean
  permissions: SysPermission[]
}

export interface SysRoleQuery extends PageQuery {}

export interface SysRoleCreate {
  name: string
  code: string
  description?: string | null
  permission_ids?: number[]
}

export interface SysRoleUpdate {
  name?: string
  description?: string | null
  permission_ids?: number[]
}

// ═══════════════════════════════════════════════════════════════
// 权限
// ═══════════════════════════════════════════════════════════════

export type PermissionAction = 'read' | 'write' | 'delete' | 'admin'

export interface SysPermission extends BaseEntity, DescribableEntity, CodedEntity {
  resource: string
  action: PermissionAction
  parent_id: number | null
}

export interface SysPermissionQuery extends PageQuery {
  parent_id?: number | null
}

export interface SysPermissionCreate {
  name: string
  code: string
  resource: string
  action: PermissionAction
  parent_id?: number | null
  description?: string | null
}

export type SysPermissionUpdate = Partial<SysPermissionCreate>

// ═══════════════════════════════════════════════════════════════
// 部门
// ═══════════════════════════════════════════════════════════════

export interface Department extends BaseEntity, DescribableEntity, CodedEntity {
  parent_id: number | null
}

export interface DepartmentQuery extends PageQuery {
  parent_id?: number | null
}

export interface DepartmentCreate {
  name: string
  code: string
  parent_id?: number | null
  description?: string | null
}

export type DepartmentUpdate = Partial<DepartmentCreate>

// ═══════════════════════════════════════════════════════════════
// 审计日志
// ═══════════════════════════════════════════════════════════════

export interface AuditLog extends BaseEntity {
  user_id: number | null
  username: string | null
  action: string
  resource_type: string
  resource_id: number | null
  detail: Record<string, unknown> | null
  ip_address: string | null
}

export interface AuditLogQuery extends PageQuery {
  user_id?: number
  action?: string
  resource_type?: string
  start_date?: string
  end_date?: string
}

// ═══════════════════════════════════════════════════════════════
// 字典类型
// ═══════════════════════════════════════════════════════════════

export interface DictType extends BaseEntity, DescribableEntity, CodedEntity {
  is_system: boolean
}

export interface DictTypeQuery extends PageQuery {}

export interface DictTypeCreate {
  name: string
  code: string
  description?: string | null
}

export type DictTypeUpdate = Partial<DictTypeCreate>

// ═══════════════════════════════════════════════════════════════
// 字典项
// ═══════════════════════════════════════════════════════════════

export interface DictItem extends BaseEntity, DescribableEntity, CodedEntity {
  dict_type_id: number
  sort_order: number
  parent_id: number | null
}

export interface DictItemQuery extends PageQuery {
  dict_type_id?: number
  parent_id?: number | null
}

export interface DictItemCreate {
  dict_type_id: number
  name: string
  code: string
  sort_order?: number
  parent_id?: number | null
  description?: string | null
}

export type DictItemUpdate = Partial<Omit<DictItemCreate, 'dict_type_id'>>
