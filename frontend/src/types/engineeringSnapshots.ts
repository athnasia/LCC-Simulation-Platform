export type SnapshotStatus = 'DRAFT' | 'READY' | 'SIMULATING' | 'COMPLETED' | 'FAILED' | 'ARCHIVED'

export type SnapshotPageMode = 'snapshot-center' | 'decision-center'

export interface SnapshotInventoryRow {
  id: number
  snapshot_code: string
  snapshot_name: string
  project_name: string
  product_name: string
  scheme_name: string
  version_label: string
  total_cost: number
  status: SnapshotStatus
  created_at: string
}