/**
 * 通用类型定义
 * 
 * 包含分页、响应、错误处理等通用类型
 */

/**
 * 分页查询参数
 */
export interface PageQuery {
  keyword?: string
  page?: number
  size?: number
}

/**
 * 分页响应结果
 */
export interface PageResult<T> {
  items: T[]
  total: number
  page: number
  size: number
  pages: number
}

/**
 * API 响应包装
 */
export interface ApiResponse<T = unknown> {
  code: string
  message: string
  data: T
}

/**
 * API 错误响应
 */
export interface ApiError {
  code: string
  message: string
  detail?: string
}

/**
 * 基础实体字段
 */
export interface BaseEntity {
  id: number
  created_at: string
  updated_at: string
  created_by: string | null
  updated_by: string | null
}

/**
 * 可激活实体
 */
export interface ActivatableEntity {
  is_active: boolean
}

/**
 * 可删除实体
 */
export interface DeletableEntity {
  is_deleted: boolean
}

/**
 * 带描述的实体
 */
export interface DescribableEntity {
  description: string | null
}

/**
 * 带编码的实体
 */
export interface CodedEntity {
  code: string
  name: string
}

/**
 * 列表项选择器
 */
export interface SelectOption {
  label: string
  value: string | number
  disabled?: boolean
}

/**
 * 树形节点
 */
export interface TreeNode<T = unknown> {
  id: number
  label: string
  children?: TreeNode<T>[]
  data?: T
}

/**
 * 表单规则类型
 */
export type FormRuleTrigger = 'blur' | 'change'

export interface FormRule {
  required?: boolean
  message?: string
  trigger?: FormRuleTrigger | FormRuleTrigger[]
  pattern?: RegExp
  min?: number
  max?: number
  validator?: (rule: unknown, value: unknown, callback: (error?: Error) => void) => void
}

/**
 * 表格列定义
 */
export interface TableColumn<T = unknown> {
  prop: keyof T | string
  label: string
  width?: number | string
  minWidth?: number | string
  fixed?: 'left' | 'right' | boolean
  sortable?: boolean | 'custom'
  align?: 'left' | 'center' | 'right'
  formatter?: (row: T, column: TableColumn<T>, cellValue: unknown, index: number) => string
}

/**
 * 操作按钮定义
 */
export interface ActionButton<T = unknown> {
  label: string
  type?: 'primary' | 'success' | 'warning' | 'danger' | 'info'
  icon?: string
  disabled?: (row: T) => boolean
  visible?: (row: T) => boolean
  onClick: (row: T) => void
}

/**
 * 对话框状态
 */
export interface DialogState<T = unknown> {
  visible: boolean
  mode: 'create' | 'edit' | 'view'
  data: T | null
}

/**
 * 加载状态
 */
export interface LoadingState {
  loading: boolean
  error: string | null
}

/**
 * 异步操作结果
 */
export type AsyncResult<T, E = ApiError> = 
  | { success: true; data: T }
  | { success: false; error: E }

/**
 * 可能为 null 的类型
 */
export type Nullable<T> = T | null

/**
 * 可能为 undefined 的类型
 */
export type Optional<T> = T | undefined

/**
 * 深度部分类型
 */
export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P]
}

/**
 * 键值对类型
 */
export type KeyValue<K extends string = string, V = unknown> = Record<K, V>

/**
 * ID 类型
 */
export type ID = number | string
