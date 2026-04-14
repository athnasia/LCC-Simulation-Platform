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
// 一、资源分类 ResourceCategory
// ═══════════════════════════════════════════════════════════════

export type ResourceType = 'MATERIAL' | 'EQUIPMENT' | 'LABOR' | 'TOOL'

export interface ResourceCategory {
  id: number
  name: string
  code: string
  resource_type: ResourceType
  parent_id: number | null
  sort_order: number
  is_active: boolean
  description: string | null
  created_at: string
  updated_at: string
}

export interface ResourceCategoryTree extends ResourceCategory {
  children: ResourceCategoryTree[]
}

export interface ResourceCategoryQuery extends PageQuery {
  resource_type?: ResourceType
  is_active?: boolean
}

export interface ResourceCategoryCreate {
  name: string
  code: string
  resource_type: ResourceType
  parent_id?: number | null
  sort_order?: number
  is_active?: boolean
  description?: string | null
}

export type ResourceCategoryUpdate = Partial<ResourceCategoryCreate>

export const resourceCategoryApi = {
  list: (params: ResourceCategoryQuery): Promise<AxiosResponse<PageResult<ResourceCategory>>> =>
    request.get('/master-data/dict-templates/categories', { params }),

  tree: (resourceType?: ResourceType): Promise<AxiosResponse<ResourceCategoryTree[]>> =>
    request.get('/master-data/dict-templates/categories/tree', { params: { resource_type: resourceType } }),

  create: (data: ResourceCategoryCreate): Promise<AxiosResponse<ResourceCategory>> =>
    request.post('/master-data/dict-templates/categories', data),

  detail: (id: number): Promise<AxiosResponse<ResourceCategory>> =>
    request.get(`/master-data/dict-templates/categories/${id}`),

  update: (id: number, data: ResourceCategoryUpdate): Promise<AxiosResponse<ResourceCategory>> =>
    request.put(`/master-data/dict-templates/categories/${id}`, data),

  remove: (id: number): Promise<AxiosResponse<void>> =>
    request.delete(`/master-data/dict-templates/categories/${id}`),
}

// ═══════════════════════════════════════════════════════════════
// 二、单位 Unit
// ═══════════════════════════════════════════════════════════════

export interface Unit {
  id: number
  name: string
  code: string
  symbol: string
  dimension_id: number
  is_base: boolean
  is_active: boolean
  description: string | null
  created_at: string
  updated_at: string
}

export interface UnitQuery extends PageQuery {
  dimension_id?: number
  is_active?: boolean
}

export const unitApi = {
  list: (params: UnitQuery): Promise<AxiosResponse<PageResult<Unit>>> =>
    request.get('/master-data/units', { params }),

  detail: (id: number): Promise<AxiosResponse<Unit>> =>
    request.get(`/master-data/units/${id}`),
}

// ═══════════════════════════════════════════════════════════════
// 三、材料 Material
// ═══════════════════════════════════════════════════════════════

export interface Material {
  id: number
  name: string
  code: string
  category_id: number | null
  pricing_unit_id: number | null
  consumption_unit_id: number | null
  unit_price: number | null
  loss_rate: number | null
  scrap_value: number | null
  substitute_group: string | null
  substitute_priority: number | null
  lcc_lifespan_months: number | null
  lcc_maintenance_cost: number | null
  dynamic_attributes: Record<string, unknown> | null
  is_active: boolean
  description: string | null
  category: Pick<ResourceCategory, 'id' | 'name' | 'code'> | null
  pricing_unit: Pick<Unit, 'id' | 'name' | 'code' | 'symbol'> | null
  consumption_unit: Pick<Unit, 'id' | 'name' | 'code' | 'symbol'> | null
  created_at: string
  updated_at: string
  created_by: string | null
  updated_by: string | null
}

export interface MaterialQuery extends PageQuery {
  category_id?: number
  is_active?: boolean
}

export interface MaterialCreate {
  name: string
  code: string
  category_id?: number | null
  pricing_unit_id?: number | null
  consumption_unit_id?: number | null
  unit_price?: number | null
  loss_rate?: number | null
  scrap_value?: number | null
  substitute_group?: string | null
  substitute_priority?: number | null
  lcc_lifespan_months?: number | null
  lcc_maintenance_cost?: number | null
  dynamic_attributes?: Record<string, unknown> | null
  is_active?: boolean
  description?: string | null
}

export type MaterialUpdate = Partial<MaterialCreate>

export const materialApi = {
  list: (params: MaterialQuery): Promise<AxiosResponse<PageResult<Material>>> =>
    request.get('/master-data/materials', { params }),

  create: (data: MaterialCreate): Promise<AxiosResponse<Material>> =>
    request.post('/master-data/materials', data),

  detail: (id: number): Promise<AxiosResponse<Material>> =>
    request.get(`/master-data/materials/${id}`),

  update: (id: number, data: MaterialUpdate): Promise<AxiosResponse<Material>> =>
    request.put(`/master-data/materials/${id}`, data),

  remove: (id: number): Promise<AxiosResponse<void>> =>
    request.delete(`/master-data/materials/${id}`),
}

// ═══════════════════════════════════════════════════════════════
// 四、设备 Equipment
// ═══════════════════════════════════════════════════════════════

export interface Equipment {
  id: number
  name: string
  code: string
  category_id: number | null
  depreciation_rate: number | null
  power_consumption: number | null
  setup_cost: number | null
  oee_target: number | null
  mtbf_hours: number | null
  defect_rate: number | null
  dynamic_attributes: Record<string, unknown> | null
  is_active: boolean
  description: string | null
  category: Pick<ResourceCategory, 'id' | 'name' | 'code'> | null
  created_at: string
  updated_at: string
  created_by: string | null
  updated_by: string | null
}

export interface EquipmentQuery extends PageQuery {
  category_id?: number
  is_active?: boolean
}

export interface EquipmentCreate {
  name: string
  code: string
  category_id?: number | null
  depreciation_rate?: number | null
  power_consumption?: number | null
  setup_cost?: number | null
  oee_target?: number | null
  mtbf_hours?: number | null
  defect_rate?: number | null
  dynamic_attributes?: Record<string, unknown> | null
  is_active?: boolean
  description?: string | null
}

export type EquipmentUpdate = Partial<EquipmentCreate>

export const equipmentApi = {
  list: (params: EquipmentQuery): Promise<AxiosResponse<PageResult<Equipment>>> =>
    request.get('/master-data/equipments', { params }),

  create: (data: EquipmentCreate): Promise<AxiosResponse<Equipment>> =>
    request.post('/master-data/equipments', data),

  detail: (id: number): Promise<AxiosResponse<Equipment>> =>
    request.get(`/master-data/equipments/${id}`),

  update: (id: number, data: EquipmentUpdate): Promise<AxiosResponse<Equipment>> =>
    request.put(`/master-data/equipments/${id}`, data),

  remove: (id: number): Promise<AxiosResponse<void>> =>
    request.delete(`/master-data/equipments/${id}`),
}

// ═══════════════════════════════════════════════════════════════
// 五、人员技能资质 Labor
// ═══════════════════════════════════════════════════════════════

export type SkillLevel = 'JUNIOR' | 'INTERMEDIATE' | 'SENIOR' | 'MASTER'

export interface Labor {
  id: number
  name: string
  code: string
  labor_type: string | null
  skill_level: SkillLevel
  hourly_rate: number | null
  qualification_code: string | null
  category_id: number | null
  is_active: boolean
  description: string | null
  category: Pick<ResourceCategory, 'id' | 'name' | 'code'> | null
  created_at: string
  updated_at: string
  created_by: string | null
  updated_by: string | null
}

export interface LaborQuery extends PageQuery {
  labor_type?: string
  skill_level?: SkillLevel
  category_id?: number
  is_active?: boolean
}

export interface LaborCreate {
  name: string
  code: string
  labor_type?: string | null
  skill_level: SkillLevel
  hourly_rate?: number | null
  qualification_code?: string | null
  category_id?: number | null
  is_active?: boolean
  description?: string | null
}

export type LaborUpdate = Partial<LaborCreate>

export const laborApi = {
  list: (params: LaborQuery): Promise<AxiosResponse<PageResult<Labor>>> =>
    request.get('/master-data/labor', { params }),

  create: (data: LaborCreate): Promise<AxiosResponse<Labor>> =>
    request.post('/master-data/labor', data),

  detail: (id: number): Promise<AxiosResponse<Labor>> =>
    request.get(`/master-data/labor/${id}`),

  update: (id: number, data: LaborUpdate): Promise<AxiosResponse<Labor>> =>
    request.put(`/master-data/labor/${id}`, data),

  remove: (id: number): Promise<AxiosResponse<void>> =>
    request.delete(`/master-data/labor/${id}`),
}

// ═══════════════════════════════════════════════════════════════
// 六、工序 Process
// ═══════════════════════════════════════════════════════════════

export type ProcessResourceType = 'MATERIAL' | 'EQUIPMENT' | 'LABOR' | 'TOOL'

export interface ProcessResource {
  id: number
  process_id: number
  resource_type: ProcessResourceType
  resource_id: number
  quantity: number
  description: string | null
  created_at: string
  updated_at: string
  created_by: string | null
  updated_by: string | null
}

export interface Process {
  id: number
  name: string
  code: string
  category_id: number | null
  standard_time: number | null
  setup_time: number | null
  is_active: boolean
  description: string | null
  category: Pick<ResourceCategory, 'id' | 'name' | 'code'> | null
  resources: ProcessResource[]
  created_at: string
  updated_at: string
  created_by: string | null
  updated_by: string | null
}

export interface ProcessQuery extends PageQuery {
  category_id?: number
  is_active?: boolean
}

export interface ProcessCreate {
  name: string
  code: string
  category_id?: number | null
  standard_time?: number | null
  setup_time?: number | null
  is_active?: boolean
  description?: string | null
  resources?: {
    resource_type: ProcessResourceType
    resource_id: number
    quantity?: number
    description?: string | null
  }[]
}

export type ProcessUpdate = Partial<Omit<ProcessCreate, 'resources'>>

export const processApi = {
  list: (params: ProcessQuery): Promise<AxiosResponse<PageResult<Process>>> =>
    request.get('/master-data/processes', { params }),

  create: (data: ProcessCreate): Promise<AxiosResponse<Process>> =>
    request.post('/master-data/processes', data),

  detail: (id: number): Promise<AxiosResponse<Process>> =>
    request.get(`/master-data/processes/${id}`),

  update: (id: number, data: ProcessUpdate): Promise<AxiosResponse<Process>> =>
    request.put(`/master-data/processes/${id}`, data),

  remove: (id: number): Promise<AxiosResponse<void>> =>
    request.delete(`/master-data/processes/${id}`),

  clone: (id: number, data: { new_name: string; new_code: string; copy_resources?: boolean }): Promise<AxiosResponse<Process>> =>
    request.post(`/master-data/processes/${id}/clone`, data),

  addResource: (processId: number, data: { resource_type: ProcessResourceType; resource_id: number; quantity?: number; description?: string | null }): Promise<AxiosResponse<ProcessResource>> =>
    request.post(`/master-data/processes/${processId}/resources`, data),

  removeResource: (processId: number, resourceId: number): Promise<AxiosResponse<void>> =>
    request.delete(`/master-data/processes/${processId}/resources/${resourceId}`),
}

// ═══════════════════════════════════════════════════════════════
// 七、能源 Energy
// ═══════════════════════════════════════════════════════════════

export type EnergyType = 'ELECTRICITY' | 'WATER' | 'GAS' | 'STEAM' | 'COMPRESSED_AIR'

export interface EnergyCalendar {
  id: number
  energy_rate_id: number
  name: string
  start_time: string
  end_time: string
  multiplier: number
  is_active: boolean
  description: string | null
  created_at: string
  updated_at: string
  created_by: string | null
  updated_by: string | null
}

export interface EnergyRate {
  id: number
  name: string
  code: string
  energy_type: EnergyType
  unit_price: number
  unit_id: number | null
  is_active: boolean
  description: string | null
  unit: Pick<Unit, 'id' | 'name' | 'code' | 'symbol'> | null
  calendars: EnergyCalendar[]
  created_at: string
  updated_at: string
  created_by: string | null
  updated_by: string | null
}

export interface EnergyRateQuery extends PageQuery {
  energy_type?: EnergyType
  is_active?: boolean
}

export interface EnergyRateCreate {
  name: string
  code: string
  energy_type: EnergyType
  unit_price: number
  unit_id?: number | null
  is_active?: boolean
  description?: string | null
  calendars?: {
    name: string
    start_time: string
    end_time: string
    multiplier?: number
    is_active?: boolean
    description?: string | null
  }[]
}

export type EnergyRateUpdate = Partial<Omit<EnergyRateCreate, 'calendars'>>

export const energyApi = {
  listRates: (params: EnergyRateQuery): Promise<AxiosResponse<PageResult<EnergyRate>>> =>
    request.get('/master-data/energy/rates', { params }),

  createRate: (data: EnergyRateCreate): Promise<AxiosResponse<EnergyRate>> =>
    request.post('/master-data/energy/rates', data),

  detailRate: (id: number): Promise<AxiosResponse<EnergyRate>> =>
    request.get(`/master-data/energy/rates/${id}`),

  updateRate: (id: number, data: EnergyRateUpdate): Promise<AxiosResponse<EnergyRate>> =>
    request.put(`/master-data/energy/rates/${id}`, data),

  removeRate: (id: number): Promise<AxiosResponse<void>> =>
    request.delete(`/master-data/energy/rates/${id}`),

  listCalendars: (params: { energy_rate_id?: number; is_active?: boolean; page?: number; size?: number }): Promise<AxiosResponse<PageResult<EnergyCalendar>>> =>
    request.get('/master-data/energy/calendars', { params }),

  createCalendar: (data: { energy_rate_id: number; name: string; start_time: string; end_time: string; multiplier?: number; is_active?: boolean; description?: string | null }): Promise<AxiosResponse<EnergyCalendar>> =>
    request.post('/master-data/energy/calendars', data),

  detailCalendar: (id: number): Promise<AxiosResponse<EnergyCalendar>> =>
    request.get(`/master-data/energy/calendars/${id}`),

  updateCalendar: (id: number, data: Partial<{ name: string; start_time: string; end_time: string; multiplier: number; is_active: boolean; description: string | null }>): Promise<AxiosResponse<EnergyCalendar>> =>
    request.put(`/master-data/energy/calendars/${id}`, data),

  removeCalendar: (id: number): Promise<AxiosResponse<void>> =>
    request.delete(`/master-data/energy/calendars/${id}`),
}
