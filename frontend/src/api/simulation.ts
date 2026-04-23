import request from '@/utils/request'
import type { AxiosResponse } from 'axios'

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
}

export interface SimulationResult {
  status: string
  snapshot_id: number
  started_at?: string
  finished_at?: string
  failed_at?: string
  virtual_started_at?: string
  virtual_finished_at?: string
  lcc_total_cost?: string
  cost_breakdown?: {
    machine_cost?: string
    labor_cost?: string
    material_cost?: string
    energy_cost?: string
    outsource_cost?: string
  }
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

export function startLccSimulation(snapshotId: number): Promise<AxiosResponse<StartSimulationResponse>> {
  return request.post(`/simulations/${snapshotId}/start`)
}

export function getSimulationStatus(snapshotId: number): Promise<AxiosResponse<SimulationStatusResponse>> {
  return request.get(`/simulations/${snapshotId}/status`)
}