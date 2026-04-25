import request from '@/utils/request'
import type { AxiosResponse } from 'axios'

export interface StartSimulationPayload {
  snapshot_id: number
  baseline_id: number
  capex: number
  base_mc: number
  annual_hours: number
}

export interface SimulationFinancialBaseline {
  id: number
  rule_name: string
  lifecycle_years: number
  discount_rate: string
  corrosion_rate: string
  risk_strategy: 'FIXED' | 'PERCENTAGE'
  risk_value: string
  eol_salvage_rate: string
  is_active: boolean
}

export interface EnergyContextRule {
  name: string
  start_time: string
  end_time: string
  multiplier: string
}

export interface EnergyContext {
  rate_code: string
  base_price: string
  rules: EnergyContextRule[]
}

export interface HourlyBreakdown {
  segment_start: string
  segment_hours: string
  electricity_rate: string
  machine_cost: string
  labor_cost: string
  energy_cost: string
}

export interface SimulationTimelineEvent {
  route_id?: number
  route_name?: string
  bom_node_id?: number
  bom_node_name?: string
  step_order?: number
  process_id?: number
  process_name?: string
  process_type?: string
  start_time?: string
  end_time?: string
  duration_hours?: string
  machine_cost?: string
  labor_cost?: string
  material_cost?: string
  energy_cost?: string
  outsource_cost?: string
  total_cost?: string
  hourly_breakdown?: HourlyBreakdown[]
  year?: number
  discount_factor?: string
  annual_opex?: string
  maintenance_cost?: string
  risk_cost?: string
  pv_opex?: string
  pv_mc?: string
  pv_rc?: string
  pv_eol?: string
  year_total_pv?: string
}

export interface SimulationResult {
  status: string
  snapshot_id: number
  simulation_type?: string
  simulation_params?: StartSimulationPayload | null
  financial_baseline?: SimulationFinancialBaseline | null
  started_at?: string
  finished_at?: string
  failed_at?: string
  virtual_started_at?: string
  virtual_finished_at?: string
  lcc_total_cost?: string
  static_total_cost?: string
  single_run_hours?: string
  annual_opex?: string
  financial_breakdown?: {
    CAPEX?: string
    OPEX?: string
    'M&R'?: string
    RISK_COST?: string
    EOL?: string
  }
  cost_breakdown?: {
    machine_cost?: string
    labor_cost?: string
    material_cost?: string
    energy_cost?: string
    outsource_cost?: string
  }
  chemical_energy_analysis?: any
  energy_context?: EnergyContext
  error_message?: string
  stack_trace?: string
  timeline_events?: SimulationTimelineEvent[]
}

export interface SimulationSnapshotData {
  total_cost?: string | number
  snapshot_code?: string
  snapshot_name?: string
  [key: string]: unknown
}

export interface StartSimulationResponse {
  message: string
  snapshot_id: number
}

export interface SimulationStatusResponse {
  snapshot_id: number
  status: string
  snapshot_code?: string
  snapshot_name?: string
  snapshot_data?: SimulationSnapshotData | null
  simulation_result: SimulationResult | null
}

export function startLccSimulation(payload: StartSimulationPayload): Promise<AxiosResponse<StartSimulationResponse>> {
  return request.post(`/simulations/${payload.snapshot_id}/start`, payload)
}

export function getSimulationStatus(snapshotId: number): Promise<AxiosResponse<SimulationStatusResponse>> {
  return request.get(`/simulations/${snapshotId}/status`)
}