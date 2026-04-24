<template>
  <div class="lcc-report-view" v-loading="loading">
    <div v-if="!emptyState" class="report-shell">
      <div class="report-header">
        <div class="header-left">
          <el-button class="back-button" text @click="handleBack">
            <el-icon><ArrowLeft /></el-icon>
            <span>返回全景快照中心</span>
          </el-button>
          <div class="title-block">
            <div class="snapshot-code">{{ snapshotCodeDisplay }}</div>
            <h1>{{ snapshotNameDisplay }}</h1>
            <div v-if="isChemicalSimulation" class="title-subline">
              化工 LCC 财务驾驶舱 / 生命周期折现推演
            </div>
            <div v-else class="title-subline">
              离散工序推演 / 虚拟时间轴成本对标
            </div>
          </div>
        </div>
        <div class="header-right">
          <el-tag class="status-tag" :type="statusTagType" effect="dark">
            {{ reportStatusText }}
          </el-tag>
        </div>
      </div>

      <template v-if="isChemicalSimulation">
        <el-row :gutter="18" class="hero-metrics chemical-metrics">
          <el-col v-for="card in financialCards" :key="card.key" :xs="24" :sm="12" :lg="Math.floor(24 / 5)">
            <div class="metric-card chemical-card" :class="card.cardClass">
              <div class="metric-label">{{ card.label }}</div>
              <div class="metric-value emphasis">{{ card.value }}</div>
              <div class="metric-subtitle">{{ card.subtitle }}</div>
            </div>
          </el-col>
        </el-row>

        <el-row :gutter="18" class="charts-grid chemical-grid">
          <el-col :xs="24" :lg="10">
            <div class="chart-card chemical-panel">
              <div class="chart-header">
                <h3>五维成本结构环形图</h3>
                <span>资本投入、运营消耗、维保、风险与处置残值占比</span>
              </div>
              <div ref="chemicalDonutChartRef" class="chart-canvas"></div>
            </div>
          </el-col>
          <el-col :xs="24" :lg="14">
            <div class="chart-card chemical-panel">
              <div class="chart-header">
                <h3>生命周期现金流堆叠柱状图</h3>
                <span>Year 0 CAPEX 起投，Year 1-N 折现 OPEX / M&amp;R / Risk / EOL</span>
              </div>
              <div ref="chemicalCashflowChartRef" class="chart-canvas chart-canvas-wide"></div>
            </div>
          </el-col>
        </el-row>

        <div class="audit-card chemical-panel">
          <div class="chart-header">
            <h3>宏观审计表</h3>
            <span>逐年现值拆解与累计净现值审计</span>
          </div>
          <el-table :data="chemicalAuditRows" border class="audit-table chemical-table">
            <el-table-column prop="yearLabel" label="年份" width="110" fixed="left" />
            <el-table-column prop="pvOpex" label="OPEX 现值" min-width="160" align="right" />
            <el-table-column prop="pvMaintenance" label="维保现值" min-width="160" align="right" />
            <el-table-column prop="pvRisk" label="风险现值" min-width="160" align="right" />
            <el-table-column prop="pvEol" label="EOL 现值" min-width="160" align="right" />
            <el-table-column prop="yearTotal" label="当年合计现值" min-width="180" align="right" />
            <el-table-column prop="cumulativeNpv" label="累计 NPV" min-width="180" align="right" fixed="right">
              <template #default="{ row }">
                <span class="total-cell">{{ row.cumulativeNpv }}</span>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </template>

      <template v-else>
        <el-row :gutter="18" class="hero-metrics">
          <el-col :xs="24" :sm="12" :lg="6">
            <div class="metric-card metric-static">
              <div class="metric-label">静态理论总成本</div>
              <div class="metric-value">{{ formatCurrency(staticTotalCost) }}</div>
              <div class="metric-subtitle">静态台账基准</div>
            </div>
          </el-col>
          <el-col :xs="24" :sm="12" :lg="6">
            <div class="metric-card metric-dynamic">
              <div class="metric-label">LCC 动态仿真总成本</div>
              <div class="metric-value emphasis">{{ formatCurrency(dynamicTotalCost) }}</div>
              <div class="metric-subtitle">虚拟时间轴推演结果</div>
            </div>
          </el-col>
          <el-col :xs="24" :sm="12" :lg="6">
            <div class="metric-card" :class="overflowCardClass">
              <div class="metric-label">仿真溢出差值</div>
              <div class="metric-value metric-delta">
                <el-icon v-if="costDeltaValue >= 0" class="delta-icon"><Top /></el-icon>
                <el-icon v-else class="delta-icon"><Bottom /></el-icon>
                <span>{{ overflowDisplay }}</span>
              </div>
              <div class="metric-subtitle">动态成本相对静态基准</div>
            </div>
          </el-col>
          <el-col :xs="24" :sm="12" :lg="6">
            <div class="metric-card metric-cycle">
              <div class="metric-label">高耗能时段命中数 / 仿真虚拟周期</div>
              <div class="metric-value compact">{{ peakHitCount }} / {{ virtualCycleDisplay }}</div>
              <div class="metric-subtitle">峰电命中次数 / 虚拟加工总时长</div>
            </div>
          </el-col>
        </el-row>

        <el-row :gutter="18" class="charts-grid">
          <el-col :xs="24" :lg="8">
            <div class="chart-card">
              <div class="chart-header">
                <h3>成本溢出瀑布图</h3>
                <span>静态基准到动态推演的膨胀链路</span>
              </div>
              <div ref="waterfallChartRef" class="chart-canvas"></div>
            </div>
          </el-col>
          <el-col :xs="24" :lg="8">
            <div class="chart-card">
              <div class="chart-header">
                <h3>结构对标双柱状图</h3>
                <span>机、人、材、电四维对标</span>
              </div>
              <div ref="comparisonChartRef" class="chart-canvas"></div>
            </div>
          </el-col>
          <el-col :xs="24" :lg="8">
            <div class="chart-card">
              <div class="chart-header">
                <h3>时间轴成本累计图</h3>
                <span>峰平谷背景与成本爬升速度</span>
              </div>
              <div ref="timelineChartRef" class="chart-canvas"></div>
            </div>
          </el-col>
        </el-row>

        <div class="audit-card">
          <div class="chart-header">
            <h3>工序审计流水表</h3>
            <span>逐工序拆解机器费、人工费、电费与异常时段命中</span>
          </div>
          <el-table :data="timelineRows" stripe border class="audit-table">
            <el-table-column prop="process_name" label="工序名称" min-width="160" fixed="left" />
            <el-table-column prop="process_type" label="工艺类型" width="120">
              <template #default="{ row }">
                <el-tag :type="row.process_type === 'OUTSOURCED' ? 'danger' : 'primary'" effect="dark">
                  {{ row.process_type === 'OUTSOURCED' ? '外协' : '自制' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="start_time_label" label="开始时间" width="180" />
            <el-table-column prop="end_time_label" label="结束时间" width="180" />
            <el-table-column prop="machine_cost" label="机器费" width="120" align="right">
              <template #default="{ row }">{{ formatCurrency(row.machine_cost) }}</template>
            </el-table-column>
            <el-table-column prop="labor_cost" label="人工费" width="120" align="right">
              <template #default="{ row }">{{ formatCurrency(row.labor_cost) }}</template>
            </el-table-column>
            <el-table-column prop="energy_cost" label="电费" width="120" align="right">
              <template #default="{ row }">{{ formatCurrency(row.energy_cost) }}</template>
            </el-table-column>
            <el-table-column prop="material_cost" label="材料费" width="120" align="right">
              <template #default="{ row }">{{ formatCurrency(row.material_cost) }}</template>
            </el-table-column>
            <el-table-column prop="total_cost" label="工序总计" width="140" align="right">
              <template #default="{ row }">
                <span class="total-cell">{{ formatCurrency(row.total_cost) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="异常备注" min-width="180" fixed="right">
              <template #default="{ row }">
                <el-tag v-if="row.hit_peak" type="danger" effect="dark">峰值电价命中</el-tag>
                <el-tag v-else-if="row.hit_valley" type="success" effect="dark">谷电窗口</el-tag>
                <span v-else class="normal-note">正常时段</span>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </template>
    </div>

    <div v-else class="empty-state">
      <el-empty description="当前快照暂无可展示的 LCC 仿真结果" />
      <el-button type="primary" @click="handleBack">返回全景快照中心</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Bottom, Top } from '@element-plus/icons-vue'
import * as echarts from 'echarts'

import { getStaticCostLedger, type StaticCostResult } from '@/api/costing'
import { modelSnapshotApi } from '@/api/engineering'
import {
  getSimulationStatus,
  type EnergyContextRule,
  type SimulationStatusResponse,
  type SimulationTimelineEvent,
} from '@/api/simulation'

interface MetricBreakdown {
  machine: number
  labor: number
  material: number
  energy: number
}

interface TimelineAuditRow {
  process_name: string
  process_type: string
  start_time_label: string
  end_time_label: string
  machine_cost: number
  labor_cost: number
  energy_cost: number
  material_cost: number
  total_cost: number
  hit_peak: boolean
  hit_valley: boolean
}

interface FinancialBreakdownMetric {
  key: 'CAPEX' | 'OPEX' | 'M&R' | 'RISK_COST' | 'EOL'
  label: string
  subtitle: string
  value: string
  rawValue: number
  displayValue: number
  cardClass: string
}

interface ChemicalAuditRow {
  yearLabel: string
  pvOpex: string
  pvMaintenance: string
  pvRisk: string
  pvEol: string
  yearTotal: string
  cumulativeNpv: string
}

const router = useRouter()
const route = useRoute()
const loading = ref(false)
const emptyState = ref(false)

const waterfallChartRef = ref<HTMLElement | null>(null)
const comparisonChartRef = ref<HTMLElement | null>(null)
const timelineChartRef = ref<HTMLElement | null>(null)
const chemicalDonutChartRef = ref<HTMLElement | null>(null)
const chemicalCashflowChartRef = ref<HTMLElement | null>(null)

let waterfallChart: echarts.ECharts | null = null
let comparisonChart: echarts.ECharts | null = null
let timelineChart: echarts.ECharts | null = null
let chemicalDonutChart: echarts.ECharts | null = null
let chemicalCashflowChart: echarts.ECharts | null = null

const snapshotId = computed(() => {
  const raw = route.params.snapshotId ?? route.params.snapshot_id
  return Number(raw)
})

const snapshotCode = ref('')
const snapshotName = ref('')
const reportStatus = ref('')
const simulationType = ref('')
const staticBreakdown = ref<MetricBreakdown>({
  machine: 0,
  labor: 0,
  material: 0,
  energy: 0,
})
const dynamicBreakdown = ref<MetricBreakdown>({
  machine: 0,
  labor: 0,
  material: 0,
  energy: 0,
})
const staticTotalCost = ref(0)
const dynamicTotalCost = ref(0)
const energyRules = ref<EnergyContextRule[]>([])
const timelineEvents = ref<SimulationTimelineEvent[]>([])
const virtualStartedAt = ref('')
const virtualFinishedAt = ref('')
const financialBreakdown = ref<Record<'CAPEX' | 'OPEX' | 'M&R' | 'RISK_COST' | 'EOL', number>>({
  CAPEX: 0,
  OPEX: 0,
  'M&R': 0,
  RISK_COST: 0,
  EOL: 0,
})

const chartTextColor = '#dbe7ff'
const chartMutedTextColor = '#7f93b8'
const gridLineColor = 'rgba(127, 147, 184, 0.16)'
const cashflowColors = {
  capex: '#6ad5ff',
  opex: '#4ce0b3',
  mr: '#ffb347',
  risk: '#ff6b8a',
  eol: '#9d8cff',
}

const snapshotCodeDisplay = computed(() => snapshotCode.value || `SNAPSHOT-${snapshotId.value}`)
const snapshotNameDisplay = computed(() => snapshotName.value || 'LCC 对标分析报告')
const isChemicalSimulation = computed(() => simulationType.value === 'PROCESS_CHEMICAL')
const reportStatusText = computed(() => {
  if (reportStatus.value === 'COMPLETED') return '仿真完成'
  if (reportStatus.value === 'FAILED') return '仿真失败'
  if (reportStatus.value === 'SIMULATING') return '推演中'
  return reportStatus.value || '未知状态'
})
const statusTagType = computed(() => {
  if (reportStatus.value === 'COMPLETED') return 'success'
  if (reportStatus.value === 'FAILED') return 'danger'
  if (reportStatus.value === 'SIMULATING') return 'warning'
  return 'info'
})

const costDeltaValue = computed(() => dynamicTotalCost.value - staticTotalCost.value)
const costDeltaRate = computed(() => {
  if (staticTotalCost.value <= 0) return 0
  return costDeltaValue.value / staticTotalCost.value
})
const overflowCardClass = computed(() => (costDeltaValue.value >= 0 ? 'metric-alert' : 'metric-good'))
const overflowDisplay = computed(() => {
  const sign = costDeltaValue.value >= 0 ? '+' : '-'
  return `${sign}${formatCurrency(Math.abs(costDeltaValue.value))} (${sign}${(Math.abs(costDeltaRate.value) * 100).toFixed(2)}%)`
})

const peakHitCount = computed(() => timelineRows.value.filter(item => item.hit_peak).length)
const virtualCycleDisplay = computed(() => {
  if (!virtualStartedAt.value || !virtualFinishedAt.value) return '--'
  const start = new Date(virtualStartedAt.value).getTime()
  const end = new Date(virtualFinishedAt.value).getTime()
  if (!Number.isFinite(start) || !Number.isFinite(end) || end < start) return '--'
  const hours = (end - start) / 3600000
  return `${hours.toFixed(2)} h`
})

const timelineRows = computed<TimelineAuditRow[]>(() => {
  return timelineEvents.value
    .filter(event => event.process_name || event.start_time)
    .map((event) => {
      const startTime = event.start_time || ''
      const matchingRule = energyRules.value.find(rule => isTimeInRule(startTime, rule))
      const multiplier = toNumber(matchingRule?.multiplier)

      return {
        process_name: event.process_name || '-',
        process_type: event.process_type || '-',
        start_time_label: formatDateTime(startTime),
        end_time_label: formatDateTime(event.end_time || ''),
        machine_cost: toNumber(event.machine_cost),
        labor_cost: toNumber(event.labor_cost),
        energy_cost: toNumber(event.energy_cost),
        material_cost: toNumber(event.material_cost),
        total_cost: toNumber(event.total_cost),
        hit_peak: multiplier >= 1.5,
        hit_valley: multiplier > 0 && multiplier < 1,
      }
    })
})

const financialCards = computed<FinancialBreakdownMetric[]>(() => {
  return [
    {
      key: 'CAPEX',
      label: 'CAPEX (初始总投资)',
      subtitle: '项目起投资本开支现值',
      value: formatCurrency(financialBreakdown.value.CAPEX),
      rawValue: financialBreakdown.value.CAPEX,
      displayValue: Math.abs(financialBreakdown.value.CAPEX),
      cardClass: 'financial-capex',
    },
    {
      key: 'OPEX',
      label: 'OPEX (全周期运营现值)',
      subtitle: '年化运营成本折现总和',
      value: formatCurrency(financialBreakdown.value.OPEX),
      rawValue: financialBreakdown.value.OPEX,
      displayValue: Math.abs(financialBreakdown.value.OPEX),
      cardClass: 'financial-opex',
    },
    {
      key: 'M&R',
      label: 'M&R (全周期维保现值)',
      subtitle: '含腐蚀老化附加',
      value: formatCurrency(financialBreakdown.value['M&R']),
      rawValue: financialBreakdown.value['M&R'],
      displayValue: Math.abs(financialBreakdown.value['M&R']),
      cardClass: 'financial-mr',
    },
    {
      key: 'RISK_COST',
      label: 'RISK COST (风险拨备现值)',
      subtitle: '固定值或 OPEX 比例拨备',
      value: formatCurrency(financialBreakdown.value.RISK_COST),
      rawValue: financialBreakdown.value.RISK_COST,
      displayValue: Math.abs(financialBreakdown.value.RISK_COST),
      cardClass: 'financial-risk',
    },
    {
      key: 'EOL',
      label: 'EOL (期末处置与残值)',
      subtitle: '残值回收或拆除处置影响',
      value: formatCurrency(financialBreakdown.value.EOL),
      rawValue: financialBreakdown.value.EOL,
      displayValue: Math.abs(financialBreakdown.value.EOL),
      cardClass: 'financial-eol',
    },
  ]
})

const chemicalAuditRows = computed<ChemicalAuditRow[]>(() => {
  let cumulativeNpv = financialBreakdown.value.CAPEX
  const rows: ChemicalAuditRow[] = [
    {
      yearLabel: 'Year 0',
      pvOpex: formatCurrency(0),
      pvMaintenance: formatCurrency(0),
      pvRisk: formatCurrency(0),
      pvEol: formatCurrency(0),
      yearTotal: formatCurrency(financialBreakdown.value.CAPEX),
      cumulativeNpv: formatCurrency(cumulativeNpv),
    },
  ]

  for (const event of timelineEvents.value) {
    if (typeof event.year !== 'number') {
      continue
    }
    const pvOpex = toNumber(event.pv_opex)
    const pvMaintenance = toNumber(event.pv_mc)
    const pvRisk = toNumber(event.pv_rc)
    const pvEol = toNumber(event.pv_eol)
    const yearTotal = toNumber(event.year_total_pv)
    cumulativeNpv += yearTotal

    rows.push({
      yearLabel: `Year ${event.year}`,
      pvOpex: formatCurrency(pvOpex),
      pvMaintenance: formatCurrency(pvMaintenance),
      pvRisk: formatCurrency(pvRisk),
      pvEol: formatCurrency(pvEol),
      yearTotal: formatCurrency(yearTotal),
      cumulativeNpv: formatCurrency(cumulativeNpv),
    })
  }

  return rows
})

function toNumber(value: unknown): number {
  if (typeof value === 'number') return value
  if (typeof value === 'string' && value.trim() !== '') {
    const parsed = Number(value)
    return Number.isFinite(parsed) ? parsed : 0
  }
  return 0
}

function formatCurrency(value: number): string {
  return `￥${value.toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`
}

function formatCompactNumber(value: number): string {
  return value.toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

function formatDateTime(value: string): string {
  if (!value) return '--'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('zh-CN', {
    hour12: false,
  })
}

function getTimeToken(value: string): string {
  if (!value) return '00:00:00'
  if (value.includes('T')) return value.split('T')[1]?.slice(0, 8) || '00:00:00'
  return value.slice(0, 8)
}

function isTimeInRule(timestamp: string, rule: EnergyContextRule): boolean {
  const current = getTimeToken(timestamp)
  const start = rule.start_time
  const end = rule.end_time

  if (start <= end) {
    return current >= start && current < end
  }
  return current >= start || current < end
}

function handleBack() {
  router.push('/costing/snapshot-center')
}

async function loadReport() {
  if (!Number.isFinite(snapshotId.value) || snapshotId.value <= 0) {
    emptyState.value = true
    return
  }

  loading.value = true
  try {
    const [simulationRes, snapshotDetailRes, staticLedgerRes] = await Promise.all([
      getSimulationStatus(snapshotId.value),
      modelSnapshotApi.detail(snapshotId.value),
      getStaticCostLedger(snapshotId.value),
    ])

    applySimulationData(simulationRes.data)
    applySnapshotDetail(snapshotDetailRes.data)
    applyStaticLedger(staticLedgerRes.data)

    if (!timelineEvents.value.length && dynamicTotalCost.value <= 0) {
      emptyState.value = true
      return
    }

    emptyState.value = false
    await nextTick()
    initCharts()
  } catch (error: any) {
    console.error('加载 LCC 报告失败:', error)
    ElMessage.error(error.response?.data?.message || '加载 LCC 报告失败')
    emptyState.value = true
  } finally {
    loading.value = false
  }
}

function applySimulationData(payload: SimulationStatusResponse) {
  reportStatus.value = payload.status
  if (payload.snapshot_code) snapshotCode.value = payload.snapshot_code
  if (payload.snapshot_name) snapshotName.value = payload.snapshot_name

  const snapshotStaticTotal = toNumber(payload.snapshot_data?.total_cost)
  if (snapshotStaticTotal > 0) {
    staticTotalCost.value = snapshotStaticTotal
  }

  const simulation = payload.simulation_result
  if (!simulation) return

  reportStatus.value = simulation.status || payload.status
  simulationType.value = simulation.simulation_type || ''
  dynamicTotalCost.value = toNumber(simulation.lcc_total_cost)
  virtualStartedAt.value = simulation.virtual_started_at || ''
  virtualFinishedAt.value = simulation.virtual_finished_at || ''
  energyRules.value = simulation.energy_context?.rules || []
  timelineEvents.value = simulation.timeline_events || []
  dynamicBreakdown.value = {
    machine: toNumber(simulation.cost_breakdown?.machine_cost),
    labor: toNumber(simulation.cost_breakdown?.labor_cost),
    material: toNumber(simulation.cost_breakdown?.material_cost),
    energy: toNumber(simulation.cost_breakdown?.energy_cost),
  }
  financialBreakdown.value = {
    CAPEX: toNumber(simulation.financial_breakdown?.CAPEX),
    OPEX: toNumber(simulation.financial_breakdown?.OPEX),
    'M&R': toNumber(simulation.financial_breakdown?.['M&R']),
    RISK_COST: toNumber(simulation.financial_breakdown?.RISK_COST),
    EOL: toNumber(simulation.financial_breakdown?.EOL),
  }
}

function applySnapshotDetail(payload: { snapshot_code: string; snapshot_name: string }) {
  snapshotCode.value = payload.snapshot_code
  snapshotName.value = payload.snapshot_name
}

function applyStaticLedger(payload: StaticCostResult) {
  if (staticTotalCost.value <= 0) {
    staticTotalCost.value = toNumber(payload.total_cost)
  }
  staticBreakdown.value = {
    machine: toNumber(payload.cost_breakdown.total_machine),
    labor: toNumber(payload.cost_breakdown.total_labor),
    material: toNumber(payload.cost_breakdown.total_material),
    energy: 0,
  }
}

function initCharts() {
  if (isChemicalSimulation.value) {
    renderChemicalDonutChart()
    renderChemicalCashflowChart()
    waterfallChart?.dispose()
    comparisonChart?.dispose()
    timelineChart?.dispose()
    waterfallChart = null
    comparisonChart = null
    timelineChart = null
    return
  }

  renderWaterfallChart()
  renderComparisonChart()
  renderTimelineChart()
  chemicalDonutChart?.dispose()
  chemicalCashflowChart?.dispose()
  chemicalDonutChart = null
  chemicalCashflowChart = null
}

function ensureChart(refEl: HTMLElement | null, current: echarts.ECharts | null): echarts.ECharts | null {
  if (!refEl) return null
  if (current) {
    current.dispose()
  }
  return echarts.init(refEl)
}

function renderWaterfallChart() {
  waterfallChart = ensureChart(waterfallChartRef.value, waterfallChart)
  if (!waterfallChart) return

  const overflow = costDeltaValue.value
  const positivePenalty = overflow > 0 ? overflow : 0
  const offsetData = [0, staticTotalCost.value, staticTotalCost.value + positivePenalty]
  const valueData = [staticTotalCost.value, positivePenalty, dynamicTotalCost.value]

  const option: echarts.EChartsOption = {
    backgroundColor: 'transparent',
    grid: { left: 52, right: 18, top: 40, bottom: 42 },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: 'rgba(7, 15, 33, 0.92)',
      borderColor: 'rgba(255,255,255,0.08)',
      textStyle: { color: chartTextColor },
      formatter: (params: any) => {
        const target = params.find((item: any) => item.seriesName === 'value')
        return `${target?.axisValueLabel}<br/>${formatCurrency(target?.value || 0)}`
      },
    },
    xAxis: {
      type: 'category',
      data: ['基础静态成本', '峰电时段溢价惩罚', '最终 LCC 动态成本'],
      axisLine: { lineStyle: { color: gridLineColor } },
      axisLabel: { color: chartMutedTextColor, interval: 0 },
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      axisLabel: { color: chartMutedTextColor, formatter: (value: number) => `￥${value}` },
      splitLine: { lineStyle: { color: gridLineColor } },
    },
    series: [
      {
        name: 'offset',
        type: 'bar',
        stack: 'total',
        itemStyle: { color: 'transparent' },
        emphasis: { itemStyle: { color: 'transparent' } },
        data: offsetData,
      },
      {
        name: 'value',
        type: 'bar',
        stack: 'total',
        barWidth: 36,
        label: {
          show: true,
          position: 'top',
          color: chartTextColor,
          formatter: (params: any) => formatCurrency(Number(params?.value ?? 0)),
        },
        itemStyle: {
          borderRadius: [10, 10, 0, 0],
          color: (params: any) => ['#29d3b2', '#ff6b6b', '#ffb347'][params.dataIndex],
        },
        data: valueData,
      },
    ],
  }

  waterfallChart.setOption(option)
}

function renderComparisonChart() {
  comparisonChart = ensureChart(comparisonChartRef.value, comparisonChart)
  if (!comparisonChart) return

  const categories = ['机器费', '人工费', '材料费', '电费']
  const staticSeries = [
    staticBreakdown.value.machine,
    staticBreakdown.value.labor,
    staticBreakdown.value.material,
    staticBreakdown.value.energy,
  ]
  const dynamicSeries = [
    dynamicBreakdown.value.machine,
    dynamicBreakdown.value.labor,
    dynamicBreakdown.value.material,
    dynamicBreakdown.value.energy,
  ]

  const option: echarts.EChartsOption = {
    backgroundColor: 'transparent',
    legend: {
      top: 4,
      textStyle: { color: chartTextColor },
      data: ['静态理论值', '动态仿真值'],
    },
    grid: { left: 48, right: 16, top: 48, bottom: 36 },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: 'rgba(7, 15, 33, 0.92)',
      borderColor: 'rgba(255,255,255,0.08)',
      textStyle: { color: chartTextColor },
    },
    xAxis: {
      type: 'category',
      data: categories,
      axisLine: { lineStyle: { color: gridLineColor } },
      axisLabel: { color: chartMutedTextColor },
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      axisLabel: { color: chartMutedTextColor, formatter: (value: number) => `￥${value}` },
      splitLine: { lineStyle: { color: gridLineColor } },
    },
    series: [
      {
        name: '静态理论值',
        type: 'bar',
        barWidth: 18,
        itemStyle: { color: '#5b8ff9', borderRadius: [8, 8, 0, 0] },
        data: staticSeries,
      },
      {
        name: '动态仿真值',
        type: 'bar',
        barWidth: 18,
        itemStyle: { color: '#f6bd16', borderRadius: [8, 8, 0, 0] },
        data: dynamicSeries,
      },
    ],
  }

  comparisonChart.setOption(option)
}

function buildMarkAreas() {
  return energyRules.value.map((rule) => {
    const multiplier = toNumber(rule.multiplier)
    const label = multiplier >= 1.5 ? '峰电时段' : multiplier < 1 ? '谷电时段' : '平电时段'
    const color = multiplier >= 1.5
      ? 'rgba(255, 107, 107, 0.16)'
      : multiplier < 1
        ? 'rgba(41, 211, 178, 0.14)'
        : 'rgba(91, 143, 249, 0.12)'

    return [
      {
        xAxis: rule.start_time.slice(0, 5),
        itemStyle: { color },
        label: {
          show: true,
          color: chartTextColor,
          formatter: label,
        },
      },
      { xAxis: rule.end_time.slice(0, 5) },
    ] as const
  }) as any
}

function renderTimelineChart() {
  timelineChart = ensureChart(timelineChartRef.value, timelineChart)
  if (!timelineChart) return

  const sortedEvents = [...timelineEvents.value].sort((left, right) => {
    return new Date(left.start_time || '').getTime() - new Date(right.start_time || '').getTime()
  })

  let cumulative = 0
  const xAxisData = sortedEvents.map(event => (event.start_time || '').slice(11, 16) || '--')
  const lineData = sortedEvents.map((event) => {
    cumulative += toNumber(event.total_cost)
    return Number(cumulative.toFixed(4))
  })

  const option: echarts.EChartsOption = {
    backgroundColor: 'transparent',
    grid: { left: 54, right: 18, top: 48, bottom: 36 },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(7, 15, 33, 0.92)',
      borderColor: 'rgba(255,255,255,0.08)',
      textStyle: { color: chartTextColor },
      formatter: (params: any) => {
        const first = params[0]
        return `${first.axisValue}<br/>累计成本：${formatCurrency(first.data || 0)}`
      },
    },
    xAxis: {
      type: 'category',
      data: xAxisData,
      boundaryGap: false,
      axisLine: { lineStyle: { color: gridLineColor } },
      axisLabel: { color: chartMutedTextColor },
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      axisLabel: { color: chartMutedTextColor, formatter: (value: number) => `￥${value}` },
      splitLine: { lineStyle: { color: gridLineColor } },
    },
    series: [
      {
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 8,
        lineStyle: { color: '#7c5cff', width: 3 },
        itemStyle: { color: '#ffd166', borderColor: '#7c5cff', borderWidth: 2 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(124, 92, 255, 0.45)' },
            { offset: 1, color: 'rgba(124, 92, 255, 0.04)' },
          ]),
        },
        markArea: {
          silent: true,
          data: buildMarkAreas(),
        },
        data: lineData,
      },
    ],
  }

  timelineChart.setOption(option)
}

function renderChemicalDonutChart() {
  chemicalDonutChart = ensureChart(chemicalDonutChartRef.value, chemicalDonutChart)
  if (!chemicalDonutChart) return

  const chartData = financialCards.value.map(card => ({
    name: card.key,
    value: card.displayValue,
    actual: card.rawValue,
  }))

  const option: echarts.EChartsOption = {
    backgroundColor: 'transparent',
    color: [cashflowColors.capex, cashflowColors.opex, cashflowColors.mr, cashflowColors.risk, cashflowColors.eol],
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(7, 15, 33, 0.96)',
      borderColor: 'rgba(255,255,255,0.08)',
      textStyle: { color: chartTextColor },
      formatter: (params: any) => {
        return `${params.name}<br/>金额：${formatCurrency(params.data.actual || 0)}<br/>占比：${params.percent}%`
      },
    },
    legend: {
      bottom: 8,
      left: 'center',
      itemWidth: 10,
      itemHeight: 10,
      textStyle: { color: chartMutedTextColor, fontSize: 12 },
      formatter: (name: string) => {
        const metric = financialCards.value.find(card => card.key === name)
        return metric ? `${metric.label.split(' ')[0]}  ${metric.value}` : name
      },
    },
    series: [
      {
        name: '五维成本结构',
        type: 'pie',
        radius: ['48%', '74%'],
        center: ['50%', '42%'],
        avoidLabelOverlap: true,
        itemStyle: {
          borderColor: '#07101f',
          borderWidth: 4,
          borderRadius: 10,
        },
        label: {
          show: true,
          color: chartTextColor,
          formatter: (params: any) => `${params.name}\n${params.percent}%`,
        },
        labelLine: {
          lineStyle: { color: 'rgba(143, 165, 210, 0.45)' },
        },
        emphasis: {
          scale: true,
          scaleSize: 6,
          itemStyle: {
            shadowBlur: 24,
            shadowColor: 'rgba(0, 0, 0, 0.38)',
          },
        },
        data: chartData,
      },
    ],
    graphic: [
      {
        type: 'text',
        left: 'center',
        top: '34%',
        style: {
          text: 'LCC NPV',
          fill: chartMutedTextColor,
          font: '500 14px sans-serif',
          align: 'center',
        },
      },
      {
        type: 'text',
        left: 'center',
        top: '40%',
        style: {
          text: formatCompactNumber(dynamicTotalCost.value),
          fill: '#f8fbff',
          font: '700 26px sans-serif',
          align: 'center',
        },
      },
    ],
  }

  chemicalDonutChart.setOption(option)
}

function renderChemicalCashflowChart() {
  chemicalCashflowChart = ensureChart(chemicalCashflowChartRef.value, chemicalCashflowChart)
  if (!chemicalCashflowChart) return

  const sortedEvents = [...timelineEvents.value]
    .filter(event => typeof event.year === 'number')
    .sort((left, right) => Number(left.year) - Number(right.year))

  const xAxisData = ['Year 0', ...sortedEvents.map(event => `Year ${event.year}`)]
  const capexSeries = [financialBreakdown.value.CAPEX, ...sortedEvents.map(() => 0)]
  const opexSeries = [0, ...sortedEvents.map(event => toNumber(event.pv_opex))]
  const mrSeries = [0, ...sortedEvents.map(event => toNumber(event.pv_mc))]
  const riskSeries = [0, ...sortedEvents.map(event => toNumber(event.pv_rc))]
  const eolSeries = [0, ...sortedEvents.map(event => toNumber(event.pv_eol))]

  const option: echarts.EChartsOption = {
    backgroundColor: 'transparent',
    legend: {
      top: 0,
      textStyle: { color: chartTextColor },
      data: ['CAPEX', 'OPEX', 'M&R', 'RISK', 'EOL'],
    },
    grid: { left: 60, right: 18, top: 56, bottom: 52 },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: 'rgba(7, 15, 33, 0.96)',
      borderColor: 'rgba(255,255,255,0.08)',
      textStyle: { color: chartTextColor },
      formatter: (params: any) => {
        const lines = [params[0]?.axisValueLabel || '']
        let total = 0
        for (const item of params) {
          total += Number(item.value || 0)
          lines.push(`${item.marker}${item.seriesName}：${formatCurrency(Number(item.value || 0))}`)
        }
        lines.push(`合计：${formatCurrency(total)}`)
        return lines.join('<br/>')
      },
    },
    xAxis: {
      type: 'category',
      data: xAxisData,
      axisLine: { lineStyle: { color: gridLineColor } },
      axisLabel: { color: chartMutedTextColor, interval: 0 },
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      axisLabel: {
        color: chartMutedTextColor,
        formatter: (value: number) => `￥${(value / 10000).toFixed(0)}w`,
      },
      splitLine: { lineStyle: { color: gridLineColor } },
      name: '现值金额',
      nameTextStyle: { color: chartMutedTextColor, padding: [0, 0, 8, 0] },
    },
    series: [
      {
        name: 'CAPEX',
        type: 'bar',
        stack: 'cashflow',
        barMaxWidth: 42,
        itemStyle: { color: cashflowColors.capex, borderRadius: [10, 10, 0, 0] },
        data: capexSeries,
      },
      {
        name: 'OPEX',
        type: 'bar',
        stack: 'cashflow',
        itemStyle: { color: cashflowColors.opex },
        data: opexSeries,
      },
      {
        name: 'M&R',
        type: 'bar',
        stack: 'cashflow',
        itemStyle: { color: cashflowColors.mr },
        data: mrSeries,
      },
      {
        name: 'RISK',
        type: 'bar',
        stack: 'cashflow',
        itemStyle: { color: cashflowColors.risk },
        data: riskSeries,
      },
      {
        name: 'EOL',
        type: 'bar',
        stack: 'cashflow',
        itemStyle: {
          color: cashflowColors.eol,
          borderRadius: [10, 10, 0, 0],
        },
        label: {
          show: true,
          position: 'top',
          color: chartTextColor,
          formatter: (params: any) => {
            return Number(params.value || 0) !== 0 ? formatCurrency(Number(params.value || 0)) : ''
          },
        },
        data: eolSeries,
      },
    ],
  }

  chemicalCashflowChart.setOption(option)
}

function resizeCharts() {
  waterfallChart?.resize()
  comparisonChart?.resize()
  timelineChart?.resize()
  chemicalDonutChart?.resize()
  chemicalCashflowChart?.resize()
}

onMounted(() => {
  void loadReport()
  window.addEventListener('resize', resizeCharts)
})

onUnmounted(() => {
  window.removeEventListener('resize', resizeCharts)
  waterfallChart?.dispose()
  comparisonChart?.dispose()
  timelineChart?.dispose()
  chemicalDonutChart?.dispose()
  chemicalCashflowChart?.dispose()
})
</script>

<style scoped>
.lcc-report-view {
  min-height: 100%;
  padding: 20px;
  background:
    radial-gradient(circle at top left, rgba(55, 97, 255, 0.15), transparent 32%),
    radial-gradient(circle at top right, rgba(255, 163, 26, 0.12), transparent 28%),
    linear-gradient(145deg, #07101f 0%, #0d172b 45%, #060b14 100%);
}

.report-shell {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.report-header,
.metric-card,
.chart-card,
.audit-card {
  border: 1px solid rgba(128, 153, 197, 0.16);
  background: rgba(8, 17, 33, 0.68);
  box-shadow: 0 18px 50px rgba(0, 0, 0, 0.28);
  backdrop-filter: blur(18px);
}

.report-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-radius: 22px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 18px;
}

.back-button {
  color: #9ab0da;
  font-weight: 500;
}

.title-block {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.title-block h1 {
  margin: 0;
  color: #f5f8ff;
  font-size: 28px;
  letter-spacing: 0.03em;
}

.title-subline {
  color: #6e89b5;
  font-size: 13px;
  letter-spacing: 0.08em;
}

.snapshot-code {
  color: #76d4ff;
  font-size: 13px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

.status-tag {
  padding: 0 14px;
  height: 32px;
}

.hero-metrics {
  margin-bottom: 0;
}

.chemical-metrics :deep(.el-col) {
  min-width: 0;
}

.metric-card {
  min-height: 150px;
  padding: 18px 20px;
  border-radius: 22px;
  overflow: hidden;
  position: relative;
}

.metric-card::after {
  content: '';
  position: absolute;
  inset: auto -30px -50px auto;
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.05);
}

.metric-static {
  box-shadow: inset 0 0 0 1px rgba(48, 201, 255, 0.1), 0 18px 50px rgba(0, 0, 0, 0.28);
}

.metric-dynamic {
  box-shadow: inset 0 0 0 1px rgba(255, 185, 60, 0.14), 0 18px 50px rgba(0, 0, 0, 0.28);
}

.metric-alert {
  box-shadow: inset 0 0 0 1px rgba(255, 82, 111, 0.14), 0 18px 50px rgba(0, 0, 0, 0.28);
}

.metric-good {
  box-shadow: inset 0 0 0 1px rgba(41, 211, 178, 0.14), 0 18px 50px rgba(0, 0, 0, 0.28);
}

.metric-cycle {
  box-shadow: inset 0 0 0 1px rgba(124, 92, 255, 0.14), 0 18px 50px rgba(0, 0, 0, 0.28);
}

.chemical-card {
  min-height: 164px;
}

.financial-capex {
  box-shadow: inset 0 0 0 1px rgba(106, 213, 255, 0.16), 0 18px 50px rgba(0, 0, 0, 0.28);
}

.financial-opex {
  box-shadow: inset 0 0 0 1px rgba(76, 224, 179, 0.16), 0 18px 50px rgba(0, 0, 0, 0.28);
}

.financial-mr {
  box-shadow: inset 0 0 0 1px rgba(255, 179, 71, 0.16), 0 18px 50px rgba(0, 0, 0, 0.28);
}

.financial-risk {
  box-shadow: inset 0 0 0 1px rgba(255, 107, 138, 0.16), 0 18px 50px rgba(0, 0, 0, 0.28);
}

.financial-eol {
  box-shadow: inset 0 0 0 1px rgba(157, 140, 255, 0.16), 0 18px 50px rgba(0, 0, 0, 0.28);
}

.metric-label {
  color: #8ea6d3;
  font-size: 13px;
  margin-bottom: 14px;
}

.metric-value {
  color: #e8f0ff;
  font-size: 34px;
  font-weight: 700;
  line-height: 1.1;
}

.metric-value.emphasis {
  color: #ffbd4c;
  font-size: 34px;
}

.metric-value.compact {
  font-size: 28px;
}

.metric-delta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 24px;
}

.metric-alert .metric-delta {
  color: #ff6b6b;
}

.metric-good .metric-delta {
  color: #29d3b2;
}

.delta-icon {
  font-size: 22px;
}

.metric-subtitle {
  margin-top: 14px;
  color: #647b9f;
  font-size: 12px;
}

.charts-grid {
  margin-top: 0;
}

.chemical-grid {
  align-items: stretch;
}

.chart-card,
.audit-card {
  border-radius: 24px;
  padding: 18px;
  height: 100%;
}

.chemical-panel {
  background:
    linear-gradient(180deg, rgba(10, 24, 43, 0.92), rgba(6, 12, 24, 0.88));
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 12px;
  margin-bottom: 16px;
}

.chart-header h3 {
  margin: 0;
  color: #f5f8ff;
  font-size: 18px;
}

.chart-header span {
  color: #6f84a7;
  font-size: 12px;
  text-align: right;
}

.chart-canvas {
  width: 100%;
  height: 360px;
}

.chart-canvas-wide {
  height: 380px;
}

.audit-card {
  padding-bottom: 20px;
  overflow: hidden;
}

.audit-table :deep(.el-table__header-wrapper th),
.audit-table :deep(.el-table__body-wrapper td) {
  background: rgba(8, 17, 33, 0.95);
  color: #dbe7ff;
  border-color: rgba(127, 147, 184, 0.14);
}

.chemical-table :deep(.el-table__header-wrapper th) {
  background: rgba(12, 28, 48, 0.96);
}

.audit-table :deep(.el-table__body tr:hover > td) {
  background: rgba(20, 38, 66, 0.96);
}

.total-cell {
  color: #ffcd73;
  font-weight: 700;
}

.normal-note {
  color: #8197bb;
}

.empty-state {
  min-height: 70vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 18px;
}

.empty-state :deep(.el-empty__description p) {
  color: #9ab0da;
}

@media (max-width: 1200px) {
  .metric-value,
  .metric-value.emphasis {
    font-size: 28px;
  }
}

@media (max-width: 768px) {
  .lcc-report-view {
    padding: 12px;
  }

  .report-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 14px;
  }

  .header-left {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .title-block h1 {
    font-size: 22px;
  }

  .chart-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .chart-header span {
    text-align: left;
  }

  .chart-canvas,
  .chart-canvas-wide {
    height: 320px;
  }
}
</style>