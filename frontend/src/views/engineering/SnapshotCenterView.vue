<template>
  <div class="snapshot-center-view">
    <div class="page-header">
      <h2>全景快照中心</h2>
      <span class="subtitle">成本核算与仿真推演数据枢纽</span>
    </div>

    <div class="page-content">
      <div class="stats-cards">
        <div class="stat-card">
          <div class="stat-icon total">
            <el-icon :size="24"><DocumentCopy /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.totalSnapshots }}</div>
            <div class="stat-label">快照总数</div>
          </div>
        </div>
        
        <div class="stat-card">
          <div class="stat-icon completed">
            <el-icon :size="24"><CircleCheck /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.simulationsCompleted }}</div>
            <div class="stat-label">已完成仿真</div>
          </div>
        </div>
        
        <div class="stat-card alert">
          <div class="stat-icon warning">
            <el-icon :size="24"><Warning /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.costAlerts }}</div>
            <div class="stat-label">异常预警</div>
          </div>
        </div>
      </div>

      <div class="filter-section">
        <el-form :inline="true" :model="filterForm" class="filter-form">
          <el-form-item label="方案/快照">
            <el-input
              v-model="filterForm.keyword"
              placeholder="请输入方案或快照名称"
              clearable
              style="width: 220px"
              @keyup.enter="handleSearch"
            />
          </el-form-item>
          
          <el-form-item label="状态">
            <el-select
              v-model="filterForm.status"
              placeholder="全部状态"
              clearable
              style="width: 140px"
            >
              <el-option label="全部" value="" />
              <el-option label="静态已生成" value="READY" />
              <el-option label="仿真推演中" value="SIMULATING" />
              <el-option label="仿真完成" value="COMPLETED" />
            </el-select>
          </el-form-item>
          
          <el-form-item label="生成时间">
            <el-date-picker
              v-model="filterForm.dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              value-format="YYYY-MM-DD"
              style="width: 260px"
            />
          </el-form-item>
          
          <el-form-item>
            <el-button type="primary" @click="handleSearch">
              <el-icon><Search /></el-icon>
              查询
            </el-button>
            <el-button @click="handleReset">
              <el-icon><Refresh /></el-icon>
              重置
            </el-button>
          </el-form-item>
        </el-form>
      </div>

      <div class="table-section">
        <div class="table-header">
          <div class="table-header-left">
            <span class="table-title">快照台账列表</span>
            <span class="table-count">共 {{ filteredSnapshots.length }} 条记录</span>
          </div>
          <div class="table-header-actions">
            <el-button
              type="primary"
              :disabled="!canCompareSelectedSnapshots"
              @click="handleCompareSnapshots"
            >
              📊 多方案 LCC 对标
            </el-button>
          </div>
        </div>
        
        <el-table
          :data="filteredSnapshots"
          v-loading="loading"
          border
          stripe
          @selection-change="handleSelectionChange"
          style="width: 100%"
        >
          <el-table-column type="selection" width="52" fixed="left" />
          <el-table-column prop="snapshot_code" label="快照编码" width="160" />
          
          <el-table-column prop="snapshot_name" label="快照名称" min-width="180">
            <template #default="{ row }">
              <div class="snapshot-name">
                <span>{{ row.snapshot_name }}</span>
                <span class="scheme-name">{{ row.scheme_name }}</span>
              </div>
            </template>
          </el-table-column>
          
          <el-table-column label="总成本" width="140" align="right">
            <template #default="{ row }">
              <span class="cost-value">{{ formatCurrency(row.total_cost) }}</span>
            </template>
          </el-table-column>
          
          <el-table-column prop="created_at" label="生成时间" width="170" />
          
          <el-table-column prop="status" label="当前状态" width="120" align="center">
            <template #default="{ row }">
              <el-tag :type="getStatusType(row.status)" :class="{ 'simulating': row.status === 'SIMULATING' }">
                <el-icon v-if="row.status === 'SIMULATING'" class="is-loading" style="margin-right: 4px">
                  <Loading />
                </el-icon>
                {{ getStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          
          <el-table-column label="操作" width="280" fixed="right" align="center">
            <template #default="{ row }">
              <div class="action-buttons">
                <template v-if="row.status === 'READY'">
                  <el-button link type="primary" @click="handleViewLedger(row)">
                    查看台账
                  </el-button>
                  <el-button type="primary" size="small" @click="handleStartSimulation(row)">
                    启动LCC仿真
                  </el-button>
                </template>
                
                <template v-else-if="row.status === 'SIMULATING'">
                  <el-button link disabled>
                    <el-icon class="is-loading"><Loading /></el-icon>
                    推演中...
                  </el-button>
                </template>
                
                <template v-else-if="row.status === 'COMPLETED'">
                  <el-button link type="primary" @click="handleViewLedger(row)">
                    查看台账
                  </el-button>
                  <el-button type="success" size="small" @click="handleViewReport(row)">
                    查看LCC报告
                  </el-button>
                </template>

                <template v-else-if="row.status === 'FAILED'">
                  <el-button link type="primary" @click="handleViewLedger(row)">
                    查看台账
                  </el-button>
                  <el-button type="danger" size="small" @click="handleStartSimulation(row)">
                    重新仿真
                  </el-button>
                </template>

                <template v-else>
                  <el-button link disabled>
                    暂不可用
                  </el-button>
                </template>
              </div>
            </template>
          </el-table-column>
        </el-table>
        
        <div class="pagination-section">
          <el-pagination
            v-model:current-page="pagination.page"
            v-model:page-size="pagination.size"
            :page-sizes="[10, 20, 50, 100]"
            :total="filteredSnapshots.length"
            layout="total, sizes, prev, pager, next, jumper"
            background
          />
        </div>
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
import { ref, reactive, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import {
  DocumentCopy,
  CircleCheck,
  Warning,
  Search,
  Refresh,
  Loading,
} from '@element-plus/icons-vue'
import { modelSnapshotApi, type ModelSnapshot } from '@/api/engineering'
import { getLccBaselines, getStaticCostLedger, type LccFinancialBaseline } from '@/api/costing'
import {
  getSimulationStatus,
  startLccSimulation,
  type StartSimulationPayload,
  type SimulationResult,
  type SimulationStatusResponse,
} from '@/api/simulation'

type SnapshotStatus = 'DRAFT' | 'READY' | 'SIMULATING' | 'COMPLETED' | 'FAILED' | 'ARCHIVED'

type SnapshotListItem = ModelSnapshot & {
  simulation_result?: SimulationResult | null
}

interface Snapshot {
  id: number
  snapshot_code: string
  snapshot_name: string
  scheme_name: string
  total_cost: number
  status: SnapshotStatus
  created_at: string
  simulation_result: SimulationResult | null
}

const router = useRouter()
const loading = ref(false)
const baselineLoading = ref(false)
const simulationSubmitting = ref(false)
const simulationDialogVisible = ref(false)
const simulationFormRef = ref<FormInstance>()
const baselineOptions = ref<LccFinancialBaseline[]>([])
const selectedSnapshotForSimulation = ref<Snapshot | null>(null)
const pollingTimers = new Map<number, number>()
let isDisposed = false

const stats = reactive({
  totalSnapshots: 0,
  simulationsCompleted: 0,
  costAlerts: 0,
})

const filterForm = reactive({
  keyword: '',
  status: '',
  dateRange: [] as string[],
})

const pagination = reactive({
  page: 1,
  size: 10,
  total: 0,
})

const snapshots = ref<Snapshot[]>([])
const allSnapshots = ref<SnapshotListItem[]>([])
const selectedSnapshots = ref<Snapshot[]>([])

interface SimulationFormState {
  baseline_id: number | undefined
  capex: number | undefined
  base_mc: number | undefined
  annual_hours: number
}

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

const filteredSnapshots = computed(() => {
  let result = [...snapshots.value]
  
  if (filterForm.keyword) {
    const keyword = filterForm.keyword.toLowerCase()
    result = result.filter(
      item =>
        item.snapshot_name.toLowerCase().includes(keyword) ||
        item.scheme_name.toLowerCase().includes(keyword) ||
        item.snapshot_code.toLowerCase().includes(keyword)
    )
  }
  
  if (filterForm.status) {
    result = result.filter(item => item.status === filterForm.status)
  }
  
  if (filterForm.dateRange && filterForm.dateRange.length === 2) {
    const [start, end] = filterForm.dateRange
    result = result.filter(item => {
      const date = item.created_at.slice(0, 10)
      return date >= start && date <= end
    })
  }
  
  return result
})

const canCompareSelectedSnapshots = computed(() => {
  return selectedSnapshots.value.length === 2 && selectedSnapshots.value.every(item => item.status === 'COMPLETED')
})

const formatCurrency = (value: number): string => {
  return '￥' + value.toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

const getStatusType = (status: string): string => {
  const map: Record<string, string> = {
    READY: 'primary',
    SIMULATING: 'warning',
    COMPLETED: 'success',
    FAILED: 'danger',
    DRAFT: 'info',
    ARCHIVED: 'info',
  }
  return map[status] || 'info'
}

const getStatusText = (status: string): string => {
  const map: Record<string, string> = {
    READY: '静态已生成',
    SIMULATING: '仿真推演中',
    COMPLETED: '仿真完成',
    FAILED: '仿真失败',
    DRAFT: '草稿',
    ARCHIVED: '已归档',
  }
  return map[status] || status
}

const syncStats = () => {
  stats.totalSnapshots = snapshots.value.length
  stats.simulationsCompleted = snapshots.value.filter(item => item.status === 'COMPLETED').length
  stats.costAlerts = snapshots.value.filter(item => item.status === 'FAILED').length
}

const normalizeStatus = (status: string): SnapshotStatus => {
  if (status === 'READY' || status === 'SIMULATING' || status === 'COMPLETED' || status === 'FAILED' || status === 'ARCHIVED') {
    return status
  }
  return 'DRAFT'
}

const toNumber = (value: unknown): number => {
  if (typeof value === 'number') {
    return value
  }
  if (typeof value === 'string' && value.trim() !== '') {
    const parsed = Number(value)
    return Number.isFinite(parsed) ? parsed : 0
  }
  return 0
}

const extractTotalCost = async (snapshot: SnapshotListItem): Promise<number> => {
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

const buildSnapshotRow = async (snapshot: SnapshotListItem): Promise<Snapshot> => {
  return {
    id: snapshot.id,
    snapshot_code: snapshot.snapshot_code,
    snapshot_name: snapshot.snapshot_name,
    scheme_name: `版本 #${snapshot.scheme_version_id}`,
    total_cost: await extractTotalCost(snapshot),
    status: normalizeStatus(snapshot.status),
    created_at: snapshot.created_at,
    simulation_result: snapshot.simulation_result ?? null,
  }
}

const resetSimulationForm = () => {
  Object.assign(simulationForm, createDefaultSimulationForm())
  simulationFormRef.value?.clearValidate()
}

const updateSnapshotRow = (snapshotId: number, patch: Partial<Snapshot>) => {
  const index = snapshots.value.findIndex(item => item.id === snapshotId)
  if (index === -1) {
    return
  }
  snapshots.value[index] = {
    ...snapshots.value[index],
    ...patch,
  }
  syncStats()
}

const clearPolling = (snapshotId: number) => {
  const timerId = pollingTimers.get(snapshotId)
  if (timerId !== undefined) {
    window.clearTimeout(timerId)
    pollingTimers.delete(snapshotId)
  }
}

const clearAllPolling = () => {
  pollingTimers.forEach((timerId) => {
    window.clearTimeout(timerId)
  })
  pollingTimers.clear()
}

const applySimulationStatus = (snapshotId: number, payload: SimulationStatusResponse) => {
  const currentRow = snapshots.value.find(item => item.id === snapshotId)
  if (!currentRow) {
    return
  }

  const nextStatus = normalizeStatus(payload.status)
  const simulationResult = payload.simulation_result ?? null
  const patch: Partial<Snapshot> = {
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

const pollSimulationStatus = async (snapshotId: number) => {
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

const loadSnapshots = async () => {
  loading.value = true
  
  try {
    const res = await modelSnapshotApi.list({ size: 100 })
    allSnapshots.value = (res.data.items || []) as SnapshotListItem[]

    const snapshotList = await Promise.all(allSnapshots.value.map(snapshot => buildSnapshotRow(snapshot)))
    if (isDisposed) {
      return
    }

    snapshots.value = snapshotList
    selectedSnapshots.value = []
    pagination.total = snapshotList.length
    syncStats()
  } catch (error: any) {
    console.error('加载快照列表失败:', error)
    ElMessage.error(error.response?.data?.message || '加载快照列表失败')
  } finally {
    loading.value = false
  }
}

const loadBaselineOptions = async () => {
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

const handleSearch = () => {
  pagination.page = 1
  selectedSnapshots.value = []
}

const handleReset = () => {
  filterForm.keyword = ''
  filterForm.status = ''
  filterForm.dateRange = []
  pagination.page = 1
  selectedSnapshots.value = []
}

const handleSelectionChange = (rows: Snapshot[]) => {
  selectedSnapshots.value = rows
}

const handleCompareSnapshots = () => {
  if (!canCompareSelectedSnapshots.value) {
    return
  }

  const [first, second] = selectedSnapshots.value
  router.push({
    path: '/engineering/lcc-compare',
    query: {
      sid1: String(first.id),
      sid2: String(second.id),
    },
  })
}

const handleViewLedger = (row: Snapshot) => {
  router.push(`/engineering/cost-ledger/${row.id}`)
}

const handleStartSimulation = (row: Snapshot) => {
  selectedSnapshotForSimulation.value = row
  resetSimulationForm()
  simulationDialogVisible.value = true
}

const handleCancelSimulationDialog = () => {
  simulationDialogVisible.value = false
  selectedSnapshotForSimulation.value = null
  resetSimulationForm()
}

const handleConfirmSimulation = async () => {
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

    await loadSnapshots()
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

const handleViewReport = (row: Snapshot) => {
  router.push(`/costing/lcc-report/${row.id}`)
}

watch(filteredSnapshots, (rows) => {
  const visibleIds = new Set(rows.map(item => item.id))
  selectedSnapshots.value = selectedSnapshots.value.filter(item => visibleIds.has(item.id))
})

onMounted(() => {
  void Promise.all([loadSnapshots(), loadBaselineOptions()])
})

onUnmounted(() => {
  isDisposed = true
  clearAllPolling()
})
</script>

<style scoped>
.snapshot-center-view {
  min-height: 100%;
  background-color: #f5f7fa;
  padding: 0;
}

.page-header {
  display: flex;
  align-items: baseline;
  gap: 12px;
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

.page-header .subtitle {
  font-size: 14px;
  color: #909399;
}

.page-content {
  padding: 20px 24px;
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-bottom: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px 24px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.stat-card.alert {
  border-left: 4px solid #f56c6c;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.stat-icon.total {
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
}

.stat-icon.completed {
  background: linear-gradient(135deg, #67c23a 0%, #85ce61 100%);
}

.stat-icon.warning {
  background: linear-gradient(135deg, #f56c6c 0%, #f78989 100%);
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
  line-height: 1.2;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.filter-section {
  background-color: #fff;
  border-radius: 8px;
  padding: 16px 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.filter-form {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.filter-form :deep(.el-form-item) {
  margin-bottom: 0;
  margin-right: 16px;
}

.filter-form :deep(.el-form-item:last-child) {
  margin-right: 0;
}

.table-section {
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  overflow: hidden;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  border-bottom: 1px solid #ebeef5;
}

.table-header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.table-header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.table-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}

.table-count {
  font-size: 13px;
  color: #909399;
}

.snapshot-name {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.snapshot-name .scheme-name {
  font-size: 12px;
  color: #909399;
}

.cost-value {
  font-weight: 600;
  color: #303133;
  font-family: 'Monaco', 'Menlo', monospace;
}

.action-buttons {
  display: flex;
  justify-content: center;
  gap: 8px;
}

.el-tag.simulating {
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}

.pagination-section {
  display: flex;
  justify-content: flex-end;
  padding: 16px 20px;
  border-top: 1px solid #ebeef5;
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
