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
// 一、项目（Project）
// ═══════════════════════════════════════════════════════════════

export interface Project {
  id: number
  name: string
  code: string
  description: string | null
  is_active: boolean
  created_at: string
  updated_at: string
  created_by: string | null
  updated_by: string | null
}

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

export const projectApi = {
  list: (params: ProjectQuery): Promise<AxiosResponse<PageResult<Project>>> =>
    request.get('/engineering/projects', { params }),

  create: (data: ProjectCreate): Promise<AxiosResponse<Project>> =>
    request.post('/engineering/projects', data),

  detail: (id: number): Promise<AxiosResponse<Project>> =>
    request.get(`/engineering/projects/${id}`),

  update: (id: number, data: ProjectUpdate): Promise<AxiosResponse<Project>> =>
    request.put(`/engineering/projects/${id}`, data),

  remove: (id: number): Promise<AxiosResponse<void>> =>
    request.delete(`/engineering/projects/${id}`),
}

// ═══════════════════════════════════════════════════════════════
// 二、产品（Product）
// ═══════════════════════════════════════════════════════════════

export interface Product {
  id: number
  name: string
  code: string
  project_id: number
  description: string | null
  attributes: Record<string, any> | null
  is_active: boolean
  created_at: string
  updated_at: string
  created_by: string | null
  updated_by: string | null
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
  attributes?: Record<string, any> | null
  is_active?: boolean
}

export type ProductUpdate = Partial<Omit<ProductCreate, 'project_id'>>

export const productApi = {
  list: (params: ProductQuery): Promise<AxiosResponse<PageResult<Product>>> =>
    request.get('/engineering/products', { params }),

  create: (data: ProductCreate): Promise<AxiosResponse<Product>> =>
    request.post('/engineering/products', data),

  detail: (id: number): Promise<AxiosResponse<Product>> =>
    request.get(`/engineering/products/${id}`),

  update: (id: number, data: ProductUpdate): Promise<AxiosResponse<Product>> =>
    request.put(`/engineering/products/${id}`, data),

  remove: (id: number): Promise<AxiosResponse<void>> =>
    request.delete(`/engineering/products/${id}`),
}

// ═══════════════════════════════════════════════════════════════
// 三、设计方案（DesignScheme）
// ═══════════════════════════════════════════════════════════════

export interface DesignScheme {
  id: number
  name: string
  code: string
  product_id: number
  description: string | null
  is_active: boolean
  created_at: string
  updated_at: string
  created_by: string | null
  updated_by: string | null
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

export type DesignSchemeUpdate = Partial<Omit<DesignSchemeCreate, 'product_id'>>

export const designSchemeApi = {
  list: (params: DesignSchemeQuery): Promise<AxiosResponse<PageResult<DesignScheme>>> =>
    request.get('/engineering/schemes', { params }),

  create: (data: DesignSchemeCreate): Promise<AxiosResponse<DesignScheme>> =>
    request.post('/engineering/schemes', data),

  detail: (id: number): Promise<AxiosResponse<DesignScheme>> =>
    request.get(`/engineering/schemes/${id}`),

  update: (id: number, data: DesignSchemeUpdate): Promise<AxiosResponse<DesignScheme>> =>
    request.put(`/engineering/schemes/${id}`, data),

  remove: (id: number): Promise<AxiosResponse<void>> =>
    request.delete(`/engineering/schemes/${id}`),
}

// ═══════════════════════════════════════════════════════════════
// 四、设计方案版本（DesignSchemeVersion）
// ═══════════════════════════════════════════════════════════════

export interface DesignSchemeVersion {
  id: number
  scheme_id: number
  version: number
  status: string
  description: string | null
  released_at: string | null
  released_by: string | null
  created_at: string
  updated_at: string
  created_by: string | null
  updated_by: string | null
}

export interface DesignSchemeVersionQuery extends PageQuery {
  scheme_id?: number
  status?: string
}

export interface DesignSchemeVersionCreate {
  scheme_id: number
  version: number
  status?: string
  description?: string | null
}

export type DesignSchemeVersionUpdate = Partial<Omit<DesignSchemeVersionCreate, 'scheme_id' | 'version'>>

export const designSchemeVersionApi = {
  list: (params: DesignSchemeVersionQuery): Promise<AxiosResponse<PageResult<DesignSchemeVersion>>> =>
    request.get('/engineering/scheme-versions', { params }),

  create: (data: DesignSchemeVersionCreate): Promise<AxiosResponse<DesignSchemeVersion>> =>
    request.post('/engineering/scheme-versions', data),

  detail: (id: number): Promise<AxiosResponse<DesignSchemeVersion>> =>
    request.get(`/engineering/scheme-versions/${id}`),

  update: (id: number, data: DesignSchemeVersionUpdate): Promise<AxiosResponse<DesignSchemeVersion>> =>
    request.put(`/engineering/scheme-versions/${id}`, data),

  remove: (id: number): Promise<AxiosResponse<void>> =>
    request.delete(`/engineering/scheme-versions/${id}`),

  release: (id: number): Promise<AxiosResponse<DesignSchemeVersion>> =>
    request.post(`/engineering/scheme-versions/${id}/release`),
}

// ═══════════════════════════════════════════════════════════════
// 五、BOM 节点（BomNode）
// ═══════════════════════════════════════════════════════════════

export interface BomNode {
  id: number
  scheme_version_id: number
  parent_id: number | null
  node_name: string
  code: string
  node_type: string
  quantity: number | null
  sort_order: number
  is_configured: boolean
  attributes: Record<string, any> | null
  description: string | null
  created_at: string
  updated_at: string
  created_by: string | null
  updated_by: string | null
}

export interface BomNodeTree extends BomNode {
  children: BomNodeTree[]
}

export interface BomNodeQuery extends PageQuery {
  scheme_version_id?: number
  parent_id?: number | null
  node_type?: string
  is_configured?: boolean
}

export interface BomNodeCreate {
  scheme_version_id: number
  parent_id?: number | null
  node_name: string
  code: string
  node_type?: string
  quantity?: number | null
  sort_order?: number
  is_configured?: boolean
  attributes?: Record<string, any> | null
  description?: string | null
}

export type BomNodeUpdate = Partial<Omit<BomNodeCreate, 'scheme_version_id'>>

export const bomNodeApi = {
  list: (params: BomNodeQuery): Promise<AxiosResponse<PageResult<BomNode>>> =>
    request.get('/engineering/bom-nodes', { params }),

  getTree: (schemeVersionId: number): Promise<AxiosResponse<BomNodeTree[]>> =>
    request.get('/engineering/bom-nodes/tree', { params: { scheme_version_id: schemeVersionId } }),

  create: (data: BomNodeCreate): Promise<AxiosResponse<BomNode>> =>
    request.post('/engineering/bom-nodes', data),

  detail: (id: number): Promise<AxiosResponse<BomNode>> =>
    request.get(`/engineering/bom-nodes/${id}`),

  update: (id: number, data: BomNodeUpdate): Promise<AxiosResponse<BomNode>> =>
    request.put(`/engineering/bom-nodes/${id}`, data),

  remove: (id: number): Promise<AxiosResponse<void>> =>
    request.delete(`/engineering/bom-nodes/${id}`),
}

// ═══════════════════════════════════════════════════════════════
// 六、零件工艺路线（ComponentProcessRoute）
// ═══════════════════════════════════════════════════════════════

export interface ComponentProcessRoute {
  id: number
  bom_node_id: number
  route_name: string
  route_code: string
  description: string | null
  is_active: boolean
  created_at: string
  updated_at: string
  created_by: string | null
  updated_by: string | null
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

export const componentProcessRouteApi = {
  list: (params: ComponentProcessRouteQuery): Promise<AxiosResponse<PageResult<ComponentProcessRoute>>> =>
    request.get('/engineering/process-routes', { params }),

  create: (data: ComponentProcessRouteCreate): Promise<AxiosResponse<ComponentProcessRoute>> =>
    request.post('/engineering/process-routes', data),

  detail: (id: number): Promise<AxiosResponse<ComponentProcessRoute>> =>
    request.get(`/engineering/process-routes/${id}`),

  update: (id: number, data: ComponentProcessRouteUpdate): Promise<AxiosResponse<ComponentProcessRoute>> =>
    request.put(`/engineering/process-routes/${id}`, data),

  remove: (id: number): Promise<AxiosResponse<void>> =>
    request.delete(`/engineering/process-routes/${id}`),
}

// ═══════════════════════════════════════════════════════════════
// 七、路线步骤（RouteStepBind）
// ═══════════════════════════════════════════════════════════════

export interface RouteStepBind {
  id: number
  route_id: number
  process_id: number
  step_order: number
  override_t_set: number | null
  override_t_run: number | null
  override_mat_params: Record<string, number> | null
  description: string | null
  created_at: string
  updated_at: string
  created_by: string | null
  updated_by: string | null
}

export interface RouteStepBindWithProcess extends RouteStepBind {
  process: {
    id: number
    name: string
    code: string
    setup_time: number | null
    standard_time: number | null
  }
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

export const routeStepBindApi = {
  list: (params: RouteStepBindQuery): Promise<AxiosResponse<PageResult<RouteStepBind>>> =>
    request.get('/engineering/route-steps', { params }),

  listWithProcess: (routeId: number): Promise<AxiosResponse<RouteStepBindWithProcess[]>> =>
    request.get(`/engineering/route-steps/with-process/${routeId}`),

  create: (data: RouteStepBindCreate): Promise<AxiosResponse<RouteStepBind>> =>
    request.post('/engineering/route-steps', data),

  detail: (id: number): Promise<AxiosResponse<RouteStepBind>> =>
    request.get(`/engineering/route-steps/${id}`),

  update: (id: number, data: RouteStepBindUpdate): Promise<AxiosResponse<RouteStepBind>> =>
    request.put(`/engineering/route-steps/${id}`, data),

  remove: (id: number): Promise<AxiosResponse<void>> =>
    request.delete(`/engineering/route-steps/${id}`),

  reorder: (routeId: number, stepIds: number[]): Promise<AxiosResponse<void>> =>
    request.post(`/engineering/route-steps/reorder`, { route_id: routeId, step_ids: stepIds }),
}

// ═══════════════════════════════════════════════════════════════
// 八、模型快照（ModelSnapshot）
// ═══════════════════════════════════════════════════════════════

export interface ModelSnapshot {
  id: number
  scheme_version_id: number
  snapshot_code: string
  snapshot_name: string
  snapshot_data: Record<string, unknown>
  status: string
  description: string | null
  created_at: string
  updated_at: string
  created_by: string | null
  updated_by: string | null
}

export interface ModelSnapshotQuery extends PageQuery {
  scheme_version_id?: number
  status?: string
}

export interface ModelSnapshotCreate {
  scheme_version_id: number
  snapshot_code: string
  snapshot_name: string
  description?: string | null
}

export type ModelSnapshotUpdate = Partial<Omit<ModelSnapshotCreate, 'scheme_version_id' | 'snapshot_code'>>

export interface GenerateSnapshotRequest {
  scheme_version_id: number
  snapshot_name: string
  description?: string | null
}

export interface GenerateSnapshotResponse {
  snapshot_id: number
  snapshot_code: string
  snapshot_name: string
  status: string
  created_at: string
}

export const modelSnapshotApi = {
  list: (params: ModelSnapshotQuery): Promise<AxiosResponse<PageResult<ModelSnapshot>>> =>
    request.get('/engineering/snapshots', { params }),

  create: (data: ModelSnapshotCreate): Promise<AxiosResponse<ModelSnapshot>> =>
    request.post('/engineering/snapshots', data),

  detail: (id: number): Promise<AxiosResponse<ModelSnapshot>> =>
    request.get(`/engineering/snapshots/${id}`),

  update: (id: number, data: ModelSnapshotUpdate): Promise<AxiosResponse<ModelSnapshot>> =>
    request.put(`/engineering/snapshots/${id}`, data),

  remove: (id: number): Promise<AxiosResponse<void>> =>
    request.delete(`/engineering/snapshots/${id}`),

  generate: (data: GenerateSnapshotRequest): Promise<AxiosResponse<GenerateSnapshotResponse>> =>
    request.post('/engineering/snapshots/generate', data),
}
