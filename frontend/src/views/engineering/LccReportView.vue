<template>
  <div class="lcc-report-view" v-loading="loading">
    <div class="report-shell" v-if="!emptyState">
      <div class="report-header">
        <div class="header-left">
          <el-button class="back-button" text @click="handleBack">
            <el-icon><ArrowLeft /></el-icon>
            <span>返回全景快照中心</span>
          </el-button>
          <div class="title-block">
            <div class="snapshot-code">{{ snapshotCodeDisplay }}</div>
            <h1>{{ snapshotNameDisplay }}</h1>
          </div>
        </div>
        <div class="header-right">
          <el-tag class="status-tag" :type="statusTagType" effect="dark">
            {{ reportStatusText }}
          </el-tag>
        </div>
      </div>

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
  type SimulationResult,
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

const router = useRouter()
const route = useRoute()
const loading = ref(false)
const emptyState = ref(false)

const waterfallChartRef = ref<HTMLElement | null>(null)
const comparisonChartRef = ref<HTMLElement | null>(null)
const timelineChartRef = ref<HTMLElement | null>(null)

let waterfallChart: echarts.ECharts | null = null
let comparisonChart: echarts.ECharts | null = null
let timelineChart: echarts.ECharts | null = null

const snapshotId = computed(() => {
  const raw = route.params.snapshotId ?? route.params.snapshot_id
  return Number(raw)
})

const snapshotCode = ref('')
const snapshotName = ref('')
const reportStatus = ref('')
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

const chartTextColor = '#dbe7ff'
const chartMutedTextColor = '#7f93b8'
const gridLineColor = 'rgba(127, 147, 184, 0.16)'

const snapshotCodeDisplay = computed(() => snapshotCode.value || `SNAPSHOT-${snapshotId.value}`)
const snapshotNameDisplay = computed(() => snapshotName.value || 'LCC 对标分析报告')
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
  return timelineEvents.value.map((event) => {
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
  renderWaterfallChart()
  renderComparisonChart()
  renderTimelineChart()
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
          formatter: ({ value }: { value: number }) => formatCurrency(value),
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
    ]
  })
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

function resizeCharts() {
  waterfallChart?.resize()
  comparisonChart?.resize()
  timelineChart?.resize()
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
  filter: blur(0px);
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
  font-size: 38px;
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

.chart-card,
.audit-card {
  border-radius: 24px;
  padding: 18px;
  height: 100%;
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

.audit-card {
  padding-bottom: 20px;
  overflow: hidden;
}

.audit-table {
  width: 100%;
}

.audit-table :deep(.el-table) {
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-current-row-bg-color: rgba(61, 123, 255, 0.12);
  --el-table-header-bg-color: rgba(13, 26, 48, 0.96);
  --el-table-fixed-box-shadow: none;
  --el-table-row-hover-bg-color: rgba(61, 123, 255, 0.14);
  --el-table-border-color: rgba(127, 147, 184, 0.14);
  --el-table-text-color: #dbe7ff;
  --el-table-header-text-color: #88a0c8;
  border-radius: 18px;
  overflow: hidden;
}

.audit-table :deep(.el-table__inner-wrapper::before) {
  background-color: rgba(127, 147, 184, 0.12);
}

.audit-table :deep(.el-table__header-wrapper),
.audit-table :deep(.el-table__body-wrapper),
.audit-table :deep(.el-table__fixed),
.audit-table :deep(.el-table__fixed-right) {
  background: transparent;
}

.audit-table :deep(.el-table th.el-table__cell) {
  background: rgba(13, 26, 48, 0.96);
  color: #8ea6d3;
  border-bottom: 1px solid rgba(127, 147, 184, 0.14);
  font-weight: 600;
  letter-spacing: 0.02em;
}

.audit-table :deep(.el-table tr) {
  background: transparent;
}

.audit-table :deep(.el-table td.el-table__cell) {
  background: rgba(8, 17, 33, 0.72);
  border-bottom: 1px solid rgba(127, 147, 184, 0.1);
  color: #dbe7ff;
  transition: background-color 0.2s ease, color 0.2s ease;
}

.audit-table :deep(.el-table--striped .el-table__body tr.el-table__row--striped td.el-table__cell) {
  background: rgba(12, 24, 44, 0.78);
}

.audit-table :deep(.el-table__body tr:hover > td.el-table__cell) {
  background: rgba(31, 64, 118, 0.46) !important;
}

.audit-table :deep(.el-table__fixed-body-wrapper tr:hover > td.el-table__cell),
.audit-table :deep(.el-table__fixed-right .el-table__fixed-body-wrapper tr:hover > td.el-table__cell) {
  background: rgba(31, 64, 118, 0.46) !important;
}

.audit-table :deep(.el-table__fixed::before),
.audit-table :deep(.el-table__fixed-right::before) {
  background-color: rgba(127, 147, 184, 0.12);
}

.audit-table :deep(.el-table__fixed .el-table__fixed-header-wrapper th.el-table__cell),
.audit-table :deep(.el-table__fixed-right .el-table__fixed-header-wrapper th.el-table__cell) {
  background: rgba(13, 26, 48, 0.98);
}

.audit-table :deep(.el-table__fixed .el-table__fixed-body-wrapper td.el-table__cell),
.audit-table :deep(.el-table__fixed-right .el-table__fixed-body-wrapper td.el-table__cell) {
  background: rgba(9, 19, 36, 0.94);
}

.audit-table :deep(.el-scrollbar__bar.is-horizontal) {
  height: 10px;
}

.audit-table :deep(.el-scrollbar__thumb) {
  background: rgba(99, 129, 187, 0.45);
  border-radius: 999px;
}

.audit-table :deep(.el-tag) {
  border: none;
}

.total-cell {
  color: #ffd166;
  font-weight: 700;
}

.normal-note {
  color: #7891bb;
}

.empty-state {
  min-height: 70vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
}

.empty-state :deep(.el-empty__description p) {
  color: #dbe7ff;
}

@media (max-width: 1440px) {
  .metric-value {
    font-size: 30px;
  }

  .metric-value.emphasis {
    font-size: 34px;
  }
}

@media (max-width: 992px) {
  .report-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }

  .header-left {
    flex-direction: column;
    align-items: flex-start;
  }

  .chart-canvas {
    height: 320px;
  }
}
</style>