import request from '@/utils/request'
import type { AxiosResponse } from 'axios'

// ═══════════════════════════════════════════════════════════════
// 成本明细类型
// ═══════════════════════════════════════════════════════════════

export interface CostDetail {
  machine_cost: number
  labor_cost: number
  material_cost: number
  outsource_cost: number
  total_cost: number
  own_cost?: CostDetail
  children_cost?: CostDetail
}

export interface BomNode {
  id: number
  node_name: string
  code: string
  node_type: string
  quantity: number | null
  parent_id: number | null
  cost_detail: CostDetail
  children?: BomNode[]
}

export interface CostBreakdown {
  total_machine: number
  total_labor: number
  total_material: number
  total_outsource: number
  total_cost: number
}

export interface StepCost {
  step_order: number
  process_id: number
  process_name: string
  process_type: string
  t_set: number | null
  t_run: number | null
  machine_cost: number
  labor_cost: number
  material_cost: number
  outsource_cost: number
  total_cost: number
}

export interface RouteCost {
  route_id: number
  route_name: string
  bom_node_id: number
  step_count: number
  machine_cost: number
  labor_cost: number
  material_cost: number
  outsource_cost: number
  total_cost: number
  step_costs: StepCost[]
}

export interface StaticCostResult {
  total_cost: number
  cost_breakdown: CostBreakdown
  annotated_bom_tree: BomNode[]
  route_costs: RouteCost[]
}

// ═══════════════════════════════════════════════════════════════
// API 函数
// ═══════════════════════════════════════════════════════════════

export function getStaticCostLedger(snapshotId: number): Promise<AxiosResponse<StaticCostResult>> {
  return request.get(`/costing/static/${snapshotId}`)
}

export interface PageResult<T> {
  items: T[]
  total: number
  page: number
  size: number
  pages: number
}

export interface LccFinancialBaseline {
  id: number
  rule_name: string
  lifecycle_years: number
  discount_rate: number
  corrosion_rate: number
  risk_strategy: 'FIXED' | 'PERCENTAGE'
  risk_value: number
  eol_salvage_rate: number
  is_active: boolean
  created_at: string
  updated_at: string
  created_by: string | null
  updated_by: string | null
}

export interface LccFinancialBaselineQuery {
  keyword?: string
  risk_strategy?: LccFinancialBaseline['risk_strategy']
  is_active?: boolean
  page?: number
  size?: number
}

export interface LccFinancialBaselineCreate {
  rule_name: string
  lifecycle_years: number
  discount_rate: number
  corrosion_rate: number
  risk_strategy: LccFinancialBaseline['risk_strategy']
  risk_value: number
  eol_salvage_rate: number
  is_active?: boolean
}

export type LccFinancialBaselineUpdate = Partial<LccFinancialBaselineCreate>

export const lccFinancialBaselineApi = {
  list: (params: LccFinancialBaselineQuery): Promise<AxiosResponse<PageResult<LccFinancialBaseline>>> =>
    request.get('/costing/lcc-financial-baselines', { params }),

  detail: (id: number): Promise<AxiosResponse<LccFinancialBaseline>> =>
    request.get(`/costing/lcc-financial-baselines/${id}`),

  create: (data: LccFinancialBaselineCreate): Promise<AxiosResponse<LccFinancialBaseline>> =>
    request.post('/costing/lcc-financial-baselines', data),

  update: (id: number, data: LccFinancialBaselineUpdate): Promise<AxiosResponse<LccFinancialBaseline>> =>
    request.put(`/costing/lcc-financial-baselines/${id}`, data),

  remove: (id: number): Promise<AxiosResponse<void>> =>
    request.delete(`/costing/lcc-financial-baselines/${id}`),
}

export function getLccBaselines(
  params: LccFinancialBaselineQuery = { is_active: true, page: 1, size: 200 },
): Promise<AxiosResponse<PageResult<LccFinancialBaseline>>> {
  return lccFinancialBaselineApi.list(params)
}
