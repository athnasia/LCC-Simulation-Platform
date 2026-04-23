/**
 * 主数据模块类型定义
 */

import type { BaseEntity, ActivatableEntity, DescribableEntity, CodedEntity, PageQuery } from './common'

// ═══════════════════════════════════════════════════════════════
// 设备
// ═══════════════════════════════════════════════════════════════

export interface Equipment extends BaseEntity, ActivatableEntity, DescribableEntity, CodedEntity {
  model: string | null
  manufacturer: string | null
  purchase_date: string | null
  depreciation_rate: number | null
  energy_consumption: number | null
  attributes: Record<string, unknown> | null
}

export interface EquipmentQuery extends PageQuery {
  is_active?: boolean
}

export interface EquipmentCreate {
  name: string
  code: string
  model?: string | null
  manufacturer?: string | null
  purchase_date?: string | null
  depreciation_rate?: number | null
  energy_consumption?: number | null
  description?: string | null
  attributes?: Record<string, unknown> | null
  is_active?: boolean
}

export type EquipmentUpdate = Partial<EquipmentCreate>

// ═══════════════════════════════════════════════════════════════
// 人员
// ═══════════════════════════════════════════════════════════════

export interface Labor extends BaseEntity, ActivatableEntity, DescribableEntity, CodedEntity {
  job_type: string
  level: string
  hourly_rate: number | null
  attributes: Record<string, unknown> | null
}

export interface LaborQuery extends PageQuery {
  job_type?: string
  level?: string
  is_active?: boolean
}

export interface LaborCreate {
  name: string
  code: string
  job_type: string
  level: string
  hourly_rate?: number | null
  description?: string | null
  attributes?: Record<string, unknown> | null
  is_active?: boolean
}

export type LaborUpdate = Partial<LaborCreate>

// ═══════════════════════════════════════════════════════════════
// 材料
// ═══════════════════════════════════════════════════════════════

export interface Material extends BaseEntity, ActivatableEntity, DescribableEntity, CodedEntity {
  category: string | null
  unit: string | null
  unit_price: number | null
  attributes: Record<string, unknown> | null
}

export interface MaterialQuery extends PageQuery {
  category?: string
  is_active?: boolean
}

export interface MaterialCreate {
  name: string
  code: string
  category?: string | null
  unit?: string | null
  unit_price?: number | null
  description?: string | null
  attributes?: Record<string, unknown> | null
  is_active?: boolean
}

export type MaterialUpdate = Partial<MaterialCreate>

// ═══════════════════════════════════════════════════════════════
// 工艺
// ═══════════════════════════════════════════════════════════════

export interface Process extends BaseEntity, ActivatableEntity, DescribableEntity, CodedEntity {
  setup_time: number | null
  standard_time: number | null
  attributes: Record<string, unknown> | null
}

export interface ProcessQuery extends PageQuery {
  is_active?: boolean
}

export interface ProcessCreate {
  name: string
  code: string
  setup_time?: number | null
  standard_time?: number | null
  description?: string | null
  attributes?: Record<string, unknown> | null
  is_active?: boolean
}

export type ProcessUpdate = Partial<ProcessCreate>

// ═══════════════════════════════════════════════════════════════
// 能源
// ═══════════════════════════════════════════════════════════════

export interface Energy extends BaseEntity, ActivatableEntity, DescribableEntity, CodedEntity {
  unit: string | null
  unit_price: number | null
  peak_price: number | null
  valley_price: number | null
  attributes: Record<string, unknown> | null
}

export interface EnergyQuery extends PageQuery {
  is_active?: boolean
}

export interface EnergyCreate {
  name: string
  code: string
  unit?: string | null
  unit_price?: number | null
  peak_price?: number | null
  valley_price?: number | null
  description?: string | null
  attributes?: Record<string, unknown> | null
  is_active?: boolean
}

export type EnergyUpdate = Partial<EnergyCreate>

// ═══════════════════════════════════════════════════════════════
// 计量单位
// ═══════════════════════════════════════════════════════════════

export interface Unit extends BaseEntity, DescribableEntity, CodedEntity {
  symbol: string | null
  category: string | null
}

export interface UnitQuery extends PageQuery {}

export interface UnitCreate {
  name: string
  code: string
  symbol?: string | null
  category?: string | null
  description?: string | null
}

export type UnitUpdate = Partial<UnitCreate>

// ═══════════════════════════════════════════════════════════════
// 单位换算
// ═══════════════════════════════════════════════════════════════

export interface UnitConversion extends BaseEntity {
  from_unit_id: number
  to_unit_id: number
  conversion_factor: number
}

export interface UnitConversionQuery extends PageQuery {
  from_unit_id?: number
  to_unit_id?: number
}

export interface UnitConversionCreate {
  from_unit_id: number
  to_unit_id: number
  conversion_factor: number
}

export type UnitConversionUpdate = Partial<UnitConversionCreate>
