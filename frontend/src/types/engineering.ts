/**
 * 工程建模模块类型定义
 */

import type { BaseEntity, ActivatableEntity, DescribableEntity, CodedEntity, PageQuery } from './common'

// ═══════════════════════════════════════════════════════════════
// 项目
// ═══════════════════════════════════════════════════════════════

export interface Project extends BaseEntity, ActivatableEntity, DescribableEntity, CodedEntity {}

export interface ProjectQuery extends PageQuery {
  is_active?: boolean
}

export interface ProjectCreate {
  name: string
  code: string
  description?: string | null
  is_active?: boolean
}

export type ProjectUpdate = Partial<ProjectCreate>

// ═══════════════════════════════════════════════════════════════
// 产品
// ═══════════════════════════════════════════════════════════════

export interface Product extends BaseEntity, ActivatableEntity, DescribableEntity, CodedEntity {
  project_id: number
  attributes: Record<string, unknown> | null
}

export interface ProductQuery extends PageQuery {
  project_id?: number
  is_active?: boolean
}

export interface ProductCreate {
  name: string
  code: string
  project_id: number
  description?: string | null
  attributes?: Record<string, unknown> | null
  is_active?: boolean
}

export type ProductUpdate = Partial<ProductCreate>

// ═══════════════════════════════════════════════════════════════
// 设计方案
// ═══════════════════════════════════════════════════════════════

export interface DesignScheme extends BaseEntity, ActivatableEntity, DescribableEntity, CodedEntity {
  product_id: number
}

export interface DesignSchemeQuery extends PageQuery {
  product_id?: number
  is_active?: boolean
}

export interface DesignSchemeCreate {
  name: string
  code: string
  product_id: number
  description?: string | null
  is_active?: boolean
}

export type DesignSchemeUpdate = Partial<DesignSchemeCreate>

// ═══════════════════════════════════════════════════════════════
// 设计方案版本
// ═══════════════════════════════════════════════════════════════

export type VersionStatus = 'DRAFT' | 'RELEASED' | 'ARCHIVED'

export interface DesignSchemeVersion extends BaseEntity, DescribableEntity {
  scheme_id: number
  version: number
  status: VersionStatus
  released_at: string | null
  released_by: string | null
}

export interface DesignSchemeVersionQuery extends PageQuery {
  scheme_id?: number
  status?: VersionStatus
}

export interface DesignSchemeVersionCreate {
  scheme_id: number
  version: number
  description?: string | null
}

// ═══════════════════════════════════════════════════════════════
// BOM 节点
// ═══════════════════════════════════════════════════════════════

export type BomNodeType = 'PART' | 'ASSEMBLY'

export interface BomNode extends BaseEntity, DescribableEntity {
  scheme_version_id: number
  parent_id: number | null
  node_name: string
  code: string
  node_type: BomNodeType
  quantity: number | null
  sort_order: number
  is_configured: boolean
  attributes: Record<string, unknown> | null
}

export interface BomNodeQuery extends PageQuery {
  scheme_version_id?: number
  parent_id?: number | null
  node_type?: BomNodeType
}

export interface BomNodeCreate {
  scheme_version_id: number
  parent_id?: number | null
  node_name: string
  code: string
  node_type: BomNodeType
  quantity?: number | null
  sort_order?: number
  description?: string | null
  attributes?: Record<string, unknown> | null
}

export type BomNodeUpdate = Partial<Omit<BomNodeCreate, 'scheme_version_id'>>

// ═══════════════════════════════════════════════════════════════
// 工艺路线
// ═══════════════════════════════════════════════════════════════

export interface ComponentProcessRoute extends BaseEntity, ActivatableEntity, DescribableEntity, CodedEntity {
  bom_node_id: number
}

export interface ComponentProcessRouteQuery extends PageQuery {
  bom_node_id?: number
  is_active?: boolean
}

export interface ComponentProcessRouteCreate {
  bom_node_id: number
  route_name: string
  route_code: string
  description?: string | null
  is_active?: boolean
}

export type ComponentProcessRouteUpdate = Partial<Omit<ComponentProcessRouteCreate, 'bom_node_id'>>

// ═══════════════════════════════════════════════════════════════
// 路线步骤绑定
// ═══════════════════════════════════════════════════════════════

export interface RouteStepBind extends BaseEntity, DescribableEntity {
  route_id: number
  process_id: number
  step_order: number
  override_t_set: number | null
  override_t_run: number | null
  override_mat_params: Record<string, number> | null
}

export interface RouteStepBindQuery extends PageQuery {
  route_id?: number
}

export interface RouteStepBindCreate {
  route_id: number
  process_id: number
  step_order: number
  override_t_set?: number | null
  override_t_run?: number | null
  override_mat_params?: Record<string, number> | null
  description?: string | null
}

export type RouteStepBindUpdate = Partial<Omit<RouteStepBindCreate, 'route_id' | 'process_id'>>

// ═══════════════════════════════════════════════════════════════
// 模型快照
// ═══════════════════════════════════════════════════════════════

export type SnapshotStatus = 'DRAFT' | 'READY' | 'ARCHIVED'

export interface ModelSnapshot extends BaseEntity, DescribableEntity {
  scheme_version_id: number
  snapshot_code: string
  snapshot_name: string
  snapshot_data: Record<string, unknown>
  status: SnapshotStatus
}

export interface ModelSnapshotQuery extends PageQuery {
  scheme_version_id?: number
  status?: SnapshotStatus
}

export interface ModelSnapshotCreate {
  scheme_version_id: number
  snapshot_name: string
  description?: string | null
}

export type ModelSnapshotUpdate = Partial<Omit<ModelSnapshotCreate, 'scheme_version_id'>>
