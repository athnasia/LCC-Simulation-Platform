<template>
  <div class="snapshot-center-view">
    <div class="page-header">
      <div>
        <h2>{{ pageTitle }}</h2>
        <span class="subtitle">{{ pageSubtitle }}</span>
      </div>
      <el-tag effect="plain" :type="pageMode === 'decision-center' ? 'success' : 'primary'">
        {{ currentScopeLabel }}
      </el-tag>
    </div>

    <div class="page-content">
      <div class="tree-panel">
        <EngineeringStructureTree
          :nodes="treeData"
          :loading="loading"
          :badge-map="snapshotCountByNodeKey"
          :current-node-key="selectedScopeNode?.key ?? null"
          title="项目快照树"
          empty-description="暂无可用项目结构"
          @node-click="handleScopeNodeClick"
        >
          <template #toolbar>
            <el-button link :disabled="!selectedScopeNode" @click="clearScopeSelection">查看全部</el-button>
          </template>
        </EngineeringStructureTree>
      </div>

      <div class="detail-panel">
        <SnapshotInventoryPanel
          :loading="loading"
          :rows="scopeSnapshots"
          :mode="pageMode"
          :scope-label="currentScopeLabel"
          @compare="handleCompareSnapshots"
          @view-ledger="handleViewLedger"
          @start-simulation="handleStartSimulation"
          @view-report="handleViewReport"
        />
      </div>

      <el-dialog
        v-model="simulationDialogVisible"
        title="配置化工 LCC 仿真参数"
        width="600px"
        destroy-on-close
      >
        <el-form
          ref="simulationFormRef"
          :model="simulationForm"
          :rules="simulationRules"
          label-width="140px"
        >
          <el-form-item label="选择财务基准" prop="baseline_id">
            <el-select
              v-model="simulationForm.baseline_id"
              placeholder="请选择 LCC 财务评估基准"
              filterable
              clearable
              class="w-full"
              :loading="baselineLoading"
            >
              <el-option
                v-for="item in baselineOptions"
                :key="item.id"
                :label="item.rule_name"
                :value="item.id"
              />
            </el-select>
          </el-form-item>

          <el-form-item label="初始总投资 CAPEX" prop="capex">
            <div class="number-input-group">
              <el-input-number
                v-model="simulationForm.capex"
                :min="0"
                :precision="2"
                controls-position="right"
                class="number-input"
              />
              <span class="unit-text">万元</span>
            </div>
            <div class="field-hint">当前快照的具体项目建厂/设备采买总造价。</div>
          </el-form-item>

          <el-form-item label="首年维保基准费" prop="base_mc">
            <div class="number-input-group">
              <el-input-number
                v-model="simulationForm.base_mc"
                :min="0"
                :precision="2"
                controls-position="right"
                class="number-input"
              />
              <span class="unit-text">万元</span>
            </div>
            <div class="field-hint">第一年的维保费基数，后续年份将按基准中的腐蚀率自动复利递增。</div>
          </el-form-item>

          <el-form-item label="年运行小时数" prop="annual_hours">
            <div class="number-input-group">
              <el-input-number
                v-model="simulationForm.annual_hours"
                :min="1"
                :precision="0"
                controls-position="right"
                class="number-input"
              />
              <span class="unit-text">小时</span>
            </div>
          </el-form-item>
        </el-form>

        <template #footer>
          <div class="dialog-footer">
            <el-button @click="handleCancelSimulationDialog">取消</el-button>
            <el-button type="primary" :loading="simulationSubmitting" @click="handleConfirmSimulation">
              确认推演
            </el-button>
          </div>
        </template>
      </el-dialog>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { modelSnapshotApi, designSchemeApi, designSchemeVersionApi, productApi, projectApi, type ModelSnapshot } from '@/api/engineering'
import { getLccBaselines, getStaticCostLedger, type LccFinancialBaseline } from '@/api/costing'
import {
  getSimulationStatus,
  startLccSimulation,
  type StartSimulationPayload,
  type SimulationResult,
  type SimulationStatusResponse,
} from '@/api/simulation'
import EngineeringStructureTree from '@/components/engineering/EngineeringStructureTree.vue'
import SnapshotInventoryPanel from '@/components/engineering/SnapshotInventoryPanel.vue'
import type { SnapshotInventoryRow, SnapshotPageMode, SnapshotStatus } from '@/types/engineeringSnapshots'
import {
  buildEngineeringStructureTree,
  createEngineeringStructureIndex,
  matchesTreeNodeScope,
  resolveSnapshotScopeRelation,
  type EngineeringStructureIndex,
  type EngineeringTreeNode,
  type SnapshotScopeRelation,
} from '@/utils/engineeringStructureTree'

type SnapshotListItem = ModelSnapshot & {
  simulation_result?: SimulationResult | null
}

type SnapshotRecord = SnapshotInventoryRow & {
  simulation_result: SimulationResult | null
  relation: SnapshotScopeRelation
}

interface SimulationFormState {
  baseline_id: number | undefined
  capex: number | undefined
  base_mc: number | undefined
  annual_hours: number
}

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const baselineLoading = ref(false)
const simulationSubmitting = ref(false)
const simulationDialogVisible = ref(false)
const simulationFormRef = ref<FormInstance>()
const baselineOptions = ref<LccFinancialBaseline[]>([])
const selectedScopeNode = ref<EngineeringTreeNode | null>(null)
const selectedSnapshotForSimulation = ref<SnapshotInventoryRow | null>(null)
const treeData = ref<EngineeringTreeNode[]>([])
const snapshotRecords = ref<SnapshotRecord[]>([])
const structureIndex = ref<EngineeringStructureIndex | null>(null)
const pollingTimers = new Map<number, number>()
let isDisposed = false

const pageMode = computed<SnapshotPageMode>(() => (route.name === 'DecisionCenter' ? 'decision-center' : 'snapshot-center'))
const pageTitle = computed(() => (pageMode.value === 'decision-center' ? '仿真结果优选与决策' : '产品快照中心'))
const pageSubtitle = computed(() => (
  pageMode.value === 'decision-center'
    ? '基于项目结构筛选候选快照，并在当前页直接完成多方案 LCC 对标决策。'
    : '基于项目结构聚合所有已生成快照，统一管理静态台账与仿真推演任务。'
))
const currentScopeLabel = computed(() => selectedScopeNode.value?.label ?? '全部项目快照')

const scopeSnapshots = computed<SnapshotInventoryRow[]>(() => {
  return snapshotRecords.value
    .filter((item) => matchesTreeNodeScope(item.relation, selectedScopeNode.value))
    .map(({ relation, simulation_result, ...row }) => row)
})

const snapshotCountByNodeKey = computed<Record<string, number>>(() => {
  const counts: Record<string, number> = {}
  for (const snapshot of snapshotRecords.value) {
    if (snapshot.relation.projectId !== null) {
      counts[`project-${snapshot.relation.projectId}`] = (counts[`project-${snapshot.relation.projectId}`] ?? 0) + 1
    }
    if (snapshot.relation.productId !== null) {
      counts[`product-${snapshot.relation.productId}`] = (counts[`product-${snapshot.relation.productId}`] ?? 0) + 1
    }
    if (snapshot.relation.schemeId !== null) {
      counts[`scheme-${snapshot.relation.schemeId}`] = (counts[`scheme-${snapshot.relation.schemeId}`] ?? 0) + 1
    }
  }
  return counts
})

const createDefaultSimulationForm = (): SimulationFormState => ({
  baseline_id: undefined,
  capex: undefined,
  base_mc: undefined,
  annual_hours: 8000,
})

const simulationForm = reactive<SimulationFormState>(createDefaultSimulationForm())

const validatePositiveNumber = (_rule: unknown, value: number | undefined, callback: (error?: Error) => void) => {
  if (value === undefined || value === null || Number.isNaN(Number(value))) {
    callback(new Error('请输入有效数值'))
    return
  }
  if (Number(value) <= 0) {
    callback(new Error('数值必须大于 0'))
    return
  }
  callback()
}

const simulationRules: FormRules<SimulationFormState> = {
  baseline_id: [{ required: true, message: '请选择财务基准', trigger: 'change' }],
  capex: [
    { required: true, message: '请输入初始总投资 CAPEX', trigger: 'change' },
    { validator: validatePositiveNumber, trigger: 'change' },
  ],
  base_mc: [
    { required: true, message: '请输入首年维保基准费', trigger: 'change' },
    { validator: validatePositiveNumber, trigger: 'change' },
  ],
  annual_hours: [
    { required: true, message: '请输入年运行小时数', trigger: 'change' },
    { validator: validatePositiveNumber, trigger: 'change' },
  ],
}

function normalizeStatus(status: string): SnapshotStatus {
  if (status === 'READY' || status === 'SIMULATING' || status === 'COMPLETED' || status === 'FAILED' || status === 'ARCHIVED') {
    return status
  }
  return 'DRAFT'
}

function toNumber(value: unknown): number {
  if (typeof value === 'number') {
    return value
  }
  if (typeof value === 'string' && value.trim() !== '') {
    const parsed = Number(value)
    return Number.isFinite(parsed) ? parsed : 0
  }
  return 0
}

async function extractTotalCost(snapshot: SnapshotListItem): Promise<number> {
  const simulationCost = toNumber(snapshot.simulation_result?.lcc_total_cost)
  if (simulationCost > 0) {
    return simulationCost
  }

  try {
    const costRes = await getStaticCostLedger(snapshot.id)
    return toNumber(costRes.data.total_cost)
  } catch {
    return 0
  }
}

async function buildSnapshotRecord(snapshot: SnapshotListItem, index: EngineeringStructureIndex): Promise<SnapshotRecord> {
  const version = index.versionsById.get(snapshot.scheme_version_id) ?? null
  const scheme = version ? index.schemesById.get(version.scheme_id) ?? null : null
  const product = scheme ? index.productsById.get(scheme.product_id) ?? null : null
  const project = product ? index.projectsById.get(product.project_id) ?? null : null

  return {
    id: snapshot.id,
    snapshot_code: snapshot.snapshot_code,
    snapshot_name: snapshot.snapshot_name,
    project_name: project?.name ?? '未关联项目',
    product_name: product?.name ?? '未关联产品',
    scheme_name: scheme?.name ?? '未关联方案',
    version_label: version ? `V${version.version}` : `版本 #${snapshot.scheme_version_id}`,
    total_cost: await extractTotalCost(snapshot),
    status: normalizeStatus(snapshot.status),
    created_at: snapshot.created_at,
    simulation_result: snapshot.simulation_result ?? null,
    relation: resolveSnapshotScopeRelation(snapshot, index),
  }
}

function resetSimulationForm() {
  Object.assign(simulationForm, createDefaultSimulationForm())
  simulationFormRef.value?.clearValidate()
}

function updateSnapshotRow(snapshotId: number, patch: Partial<SnapshotRecord>) {
  const index = snapshotRecords.value.findIndex((item) => item.id === snapshotId)
  if (index === -1) {
    return
  }

  snapshotRecords.value[index] = {
    ...snapshotRecords.value[index],
    ...patch,
  }
}

function clearPolling(snapshotId: number) {
  const timerId = pollingTimers.get(snapshotId)
  if (timerId !== undefined) {
    window.clearTimeout(timerId)
    pollingTimers.delete(snapshotId)
  }
}

function clearAllPolling() {
  pollingTimers.forEach((timerId) => {
    window.clearTimeout(timerId)
  })
  pollingTimers.clear()
}

function applySimulationStatus(snapshotId: number, payload: SimulationStatusResponse) {
  const currentRow = snapshotRecords.value.find((item) => item.id === snapshotId)
  if (!currentRow) {
    return
  }

  const nextStatus = normalizeStatus(payload.status)
  const simulationResult = payload.simulation_result ?? null
  const patch: Partial<SnapshotRecord> = {
    simulation_result: simulationResult,
  }

  if (!(currentRow.status === 'SIMULATING' && nextStatus === 'READY')) {
    patch.status = nextStatus
  }

  if (simulationResult?.lcc_total_cost !== undefined) {
    patch.total_cost = toNumber(simulationResult.lcc_total_cost)
  }

  updateSnapshotRow(snapshotId, patch)
}

async function pollSimulationStatus(snapshotId: number) {
  if (isDisposed) {
    clearPolling(snapshotId)
    return
  }

  try {
    const { data } = await getSimulationStatus(snapshotId)
    applySimulationStatus(snapshotId, data)

    if (data.status === 'COMPLETED' || data.status === 'FAILED') {
      clearPolling(snapshotId)
      if (data.status === 'FAILED') {
        ElMessage.error(data.simulation_result?.error_message || `快照 ${snapshotId} 仿真失败`)
      }
      return
    }
  } catch (error) {
    console.error('轮询仿真状态失败:', error)
  }

  if (!isDisposed) {
    const timerId = window.setTimeout(() => {
      void pollSimulationStatus(snapshotId)
    }, 3000)
    pollingTimers.set(snapshotId, timerId)
  }
}

async function loadStructureAndSnapshots() {
  loading.value = true
  try {
    const [projectsRes, productsRes, schemesRes, versionsRes, snapshotsRes] = await Promise.all([
      projectApi.list({ size: 200 }),
      productApi.list({ size: 500 }),
      designSchemeApi.list({ size: 500 }),
      designSchemeVersionApi.list({ size: 500 }),
      modelSnapshotApi.list({ size: 500 }),
    ])

    const projects = projectsRes.data.items || []
    const products = productsRes.data.items || []
    const schemes = schemesRes.data.items || []
    const versions = versionsRes.data.items || []
    const index = createEngineeringStructureIndex(projects, products, schemes, versions)

    structureIndex.value = index
    treeData.value = buildEngineeringStructureTree(projects, products, schemes)
    snapshotRecords.value = await Promise.all(
      ((snapshotsRes.data.items || []) as SnapshotListItem[]).map((snapshot) => buildSnapshotRecord(snapshot, index)),
    )
  } catch (error: any) {
    console.error('加载快照结构失败:', error)
    ElMessage.error(error.response?.data?.message || '加载快照结构失败')
  } finally {
    loading.value = false
  }
}

async function loadBaselineOptions() {
  baselineLoading.value = true
  try {
    const res = await getLccBaselines({ is_active: true, page: 1, size: 200 })
    baselineOptions.value = res.data.items ?? []
  } catch (error: any) {
    console.error('加载 LCC 财务评估基准失败:', error)
    ElMessage.error(error.response?.data?.message || '加载 LCC 财务评估基准失败')
  } finally {
    baselineLoading.value = false
  }
}

function handleScopeNodeClick(node: EngineeringTreeNode) {
  selectedScopeNode.value = node
}

function clearScopeSelection() {
  selectedScopeNode.value = null
}

function handleCompareSnapshots(rows: SnapshotInventoryRow[]) {
  if (rows.length !== 2) {
    return
  }

  const [first, second] = rows
  router.push({
    path: '/engineering/lcc-compare',
    query: {
      sid1: String(first.id),
      sid2: String(second.id),
      source: pageMode.value,
    },
  })
}

function handleViewLedger(row: SnapshotInventoryRow) {
  router.push(`/engineering/cost-ledger/${row.id}`)
}

function handleStartSimulation(row: SnapshotInventoryRow) {
  selectedSnapshotForSimulation.value = row
  resetSimulationForm()
  simulationDialogVisible.value = true
}

function handleCancelSimulationDialog() {
  simulationDialogVisible.value = false
  selectedSnapshotForSimulation.value = null
  resetSimulationForm()
}

async function handleConfirmSimulation() {
  const currentRow = selectedSnapshotForSimulation.value
  if (!currentRow) {
    return
  }

  const valid = await simulationFormRef.value?.validate().catch(() => false)
  if (!valid) {
    return
  }

  const payload: StartSimulationPayload = {
    snapshot_id: currentRow.id,
    baseline_id: Number(simulationForm.baseline_id),
    capex: Number(simulationForm.capex),
    base_mc: Number(simulationForm.base_mc),
    annual_hours: Number(simulationForm.annual_hours),
  }

  simulationSubmitting.value = true
  try {
    clearPolling(currentRow.id)
    await startLccSimulation(payload)

    simulationDialogVisible.value = false
    selectedSnapshotForSimulation.value = null
    resetSimulationForm()

    updateSnapshotRow(currentRow.id, {
      status: 'SIMULATING',
      simulation_result: {
        status: 'SIMULATING',
        snapshot_id: currentRow.id,
        simulation_params: payload,
      },
    })

    ElMessage.success({
      message: `快照 ${currentRow.snapshot_code} 已成功投递至仿真队列`,
      duration: 3000,
    })

    const timerId = window.setTimeout(() => {
      void pollSimulationStatus(currentRow.id)
    }, 3000)
    pollingTimers.set(currentRow.id, timerId)
  } catch (error) {
    console.error('启动仿真失败:', error)
  } finally {
    simulationSubmitting.value = false
  }
}

function handleViewReport(row: SnapshotInventoryRow) {
  router.push(`/costing/lcc-report/${row.id}`)
}

onMounted(() => {
  void Promise.all([loadStructureAndSnapshots(), loadBaselineOptions()])
})

onUnmounted(() => {
  isDisposed = true
  clearAllPolling()
})
</script>

<style scoped>
.snapshot-center-view {
  height: 100%;
  display: flex;
  flex-direction: column;
  background-color: #f5f7fa;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  padding: 20px 24px;
  background-color: #fff;
  border-bottom: 1px solid #e4e7ed;
}

.page-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.subtitle {
  display: inline-block;
  margin-top: 4px;
  font-size: 14px;
  color: #909399;
}

.page-content {
  flex: 1;
  min-height: 0;
  display: flex;
  gap: 16px;
  padding: 20px 24px;
}

.tree-panel,
.detail-panel {
  min-height: 0;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.tree-panel {
  width: 360px;
  min-width: 320px;
  padding: 16px;
}

.detail-panel {
  flex: 1;
  padding: 20px;
  overflow: auto;
}

.number-input-group {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}

.number-input {
  flex: 1;
}

.unit-text {
  color: #606266;
  white-space: nowrap;
}

.field-hint {
  font-size: 12px;
  color: #909399;
  line-height: 1.5;
  margin-top: 6px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

:deep(.el-table) {
  --el-table-header-bg-color: #fafafa;
}

:deep(.el-table th.el-table__cell) {
  font-weight: 600;
  color: #606266;
}

:deep(.el-table .el-table__row:hover > td.el-table__cell) {
  background-color: #f5f7fa;
}
</style>
