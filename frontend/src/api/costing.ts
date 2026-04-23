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
