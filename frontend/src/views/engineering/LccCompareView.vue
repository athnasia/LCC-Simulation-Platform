<template>
  <div class="lcc-compare-view" v-loading="loading">
    <div v-if="!errorMessage && snapshotA && snapshotB" class="compare-shell">
      <div class="compare-header">
        <div class="header-left">
          <el-button class="back-button" text @click="handleBack">
            <el-icon><ArrowLeft /></el-icon>
            <span>返回全景快照中心</span>
          </el-button>
          <div class="title-block">
            <div class="eyebrow">PROCESS_CHEMICAL / LCC A-B TEST</div>
            <h1>LCC 对标与决策大屏</h1>
            <p>以生命周期折现现值为主线，对双快照进行推优决策。</p>
          </div>
        </div>
        <div class="header-right">
          <el-tag effect="dark" type="info">双方案对标</el-tag>
          <el-tag effect="dark" type="success">{{ recommendationTag }}</el-tag>
        </div>
      </div>

      <div class="summary-grid">
        <section class="summary-card scheme-a">
          <div class="summary-head">
            <span class="summary-badge">方案 1</span>
            <div class="summary-head-side">
              <span class="summary-code">{{ snapshotA.snapshot.snapshot_code }}</span>
              <span class="summary-trend baseline">基准方案</span>
            </div>
          </div>
          <div class="summary-value">{{ formatWan(snapshotA.totalCost) }}</div>
          <div class="summary-title">{{ snapshotA.snapshot.snapshot_name }}</div>
          <div class="summary-meta">{{ snapshotA.ruleName }} / {{ snapshotA.lifecycleLabel }}</div>
        </section>

        <section class="summary-card scheme-b">
          <div class="summary-head">
            <span class="summary-badge">方案 2</span>
            <div class="summary-head-side">
              <span class="summary-code">{{ snapshotB.snapshot.snapshot_code }}</span>
              <span v-if="rightCardTrend" class="summary-trend" :class="`is-${rightCardTrend.direction}`">
                <span class="summary-trend-arrow">{{ rightCardTrend.arrow }}</span>
                <span>{{ rightCardTrend.text }}</span>
              </span>
            </div>
          </div>
          <div class="summary-value">{{ formatWan(snapshotB.totalCost) }}</div>
          <div class="summary-title">{{ snapshotB.snapshot.snapshot_name }}</div>
          <div class="summary-meta">{{ snapshotB.ruleName }} / {{ snapshotB.lifecycleLabel }}</div>
        </section>

        <section class="summary-card scheme-delta">
          <div class="summary-head">
            <span class="summary-badge">成本对比摘要</span>
            <span class="summary-code">{{ cheaperSnapshot?.slot }} 优势</span>
          </div>
          <div class="summary-value accent">{{ formatWan(costDelta) }}</div>
          <div class="summary-title">预计成本差额</div>
          <div class="summary-meta">{{ recommendationText }}</div>
        </section>
      </div>

      <div class="content-grid">
        <section class="panel chart-panel">
          <div class="panel-header">
            <div>
              <h3>五维 LCC 成本分解对标</h3>
              <p>CAPEX / OPEX / M&amp;R / RISK / EOL 分组柱状图</p>
            </div>
            <div class="panel-note">单位：万元</div>
          </div>
          <div ref="compareChartRef" class="chart-canvas"></div>

          <div class="resource-delta-card">
            <div class="resource-delta-header">
              <div>
                <h4>机 / 人 / 料 差异摘要</h4>
                <p>以方案 A 为基准，补充展示人员、设备、材料三类直接成本差异。</p>
              </div>
              <span class="panel-note">单位：万元</span>
            </div>

            <div class="resource-delta-grid">
              <div v-for="item in directCostDeltaRows" :key="item.key" class="resource-delta-item">
                <div class="resource-delta-top">
                  <span class="resource-delta-label">{{ item.label }}</span>
                  <span class="resource-delta-trend" :class="`is-${item.direction}`">
                    <span class="resource-delta-arrow">{{ item.arrow }}</span>
                    <span>{{ item.deltaRateText }}</span>
                  </span>
                </div>
                <div class="resource-delta-values">
                  <span>A {{ formatWan(item.aValue) }}</span>
                  <span>B {{ formatWan(item.bValue) }}</span>
                </div>
                <div class="resource-delta-footer">{{ item.winnerLabel }}，差额 {{ item.deltaText }}</div>
              </div>
            </div>
          </div>
        </section>

        <section class="panel insight-panel">
          <div class="panel-header">
            <div>
              <h3>执行摘要</h3>
              <p>成本结构差异与主推荐口径</p>
            </div>
          </div>

          <div class="insight-kpis">
            <div class="kpi-block">
              <span class="kpi-label">推荐方案</span>
              <strong>{{ recommendationTag }}</strong>
            </div>
            <div class="kpi-block">
              <span class="kpi-label">节约比例</span>
              <strong>{{ formatPercent(costDeltaRate) }}</strong>
            </div>
            <div class="kpi-block">
              <span class="kpi-label">最大分项差异</span>
              <strong>{{ topDeltaCategoryLabel }}</strong>
            </div>
          </div>

          <div class="delta-list">
            <div v-for="item in categoryDeltaRows" :key="item.key" class="delta-row">
              <div>
                <div class="delta-label">{{ item.label }}</div>
                <div class="delta-helper">{{ item.winnerLabel }}</div>
              </div>
              <div class="delta-value">{{ item.deltaText }}</div>
            </div>
          </div>
        </section>
      </div>

      <section class="panel decision-panel">
        <div class="panel-header decision-header">
          <div>
            <h3>版本推优决策区</h3>
            <p>点击 A/B 任一方案卡片后，弹出确认框；确认后即生成新版本。</p>
          </div>
          <div class="decision-status">当前选择：{{ selectedSnapshot?.slot || '--' }}</div>
        </div>

        <div class="decision-grid">
          <button
            type="button"
            class="decision-card"
            :class="{ selected: selectedSnapshotId === snapshotA.snapshot.id, recommended: cheaperSnapshot?.snapshot.id === snapshotA.snapshot.id }"
            :disabled="promoting"
            @click="handleSelect(snapshotA.snapshot.id)"
          >
            <div class="decision-card-head">
              <span>方案 1</span>
              <el-tag v-if="cheaperSnapshot?.snapshot.id === snapshotA.snapshot.id" type="success" effect="dark">推荐</el-tag>
            </div>
            <strong>{{ formatWan(snapshotA.totalCost) }}</strong>
            <span>{{ snapshotA.snapshot.snapshot_name }}</span>
            <small>{{ snapshotA.snapshot.snapshot_code }}</small>
          </button>

          <button
            type="button"
            class="decision-card"
            :class="{ selected: selectedSnapshotId === snapshotB.snapshot.id, recommended: cheaperSnapshot?.snapshot.id === snapshotB.snapshot.id }"
            :disabled="promoting"
            @click="handleSelect(snapshotB.snapshot.id)"
          >
            <div class="decision-card-head">
              <span>方案 2</span>
              <el-tag v-if="cheaperSnapshot?.snapshot.id === snapshotB.snapshot.id" type="success" effect="dark">推荐</el-tag>
            </div>
            <strong>{{ formatWan(snapshotB.totalCost) }}</strong>
            <span>{{ snapshotB.snapshot.snapshot_name }}</span>
            <small>{{ snapshotB.snapshot.snapshot_code }}</small>
          </button>
        </div>

        <div class="decision-output">
          <div class="decision-copy-title">自动生成的版本描述</div>
          <div class="decision-copy">{{ decisionDescription }}</div>
        </div>

        <div v-if="promotionResult" class="promotion-result">
          <span>{{ promotionResult.message }}</span>
          <span>版本记录 #{{ promotionResult.version_id }} / V{{ promotionResult.version_number }} / {{ promotionResult.status }}</span>
        </div>

        <div class="decision-actions">
          <el-button @click="handleBack">取消返回</el-button>
        </div>
      </section>
    </div>

    <div v-else class="state-shell">
      <el-empty :description="errorMessage || '未找到可用于LCC 对标的双快照数据'" />
      <el-button type="primary" @click="handleBack">返回全景快照中心</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import * as echarts from 'echarts'

import { getStaticCostLedger, type CostBreakdown as StaticCostBreakdown } from '@/api/costing'
import {
  modelSnapshotApi,
  type ModelSnapshot,
  type PromoteSnapshotToVersionResponse,
} from '@/api/engineering'

type BreakdownKey = 'CAPEX' | 'OPEX' | 'M&R' | 'RISK_COST' | 'EOL'
type DirectCostKey = 'labor' | 'machine' | 'material'

interface CompareSnapshotViewModel {
  slot: 'A' | 'B'
  snapshot: ModelSnapshot
  totalCost: number
  breakdown: Record<BreakdownKey, number>
  directCosts: Record<DirectCostKey, number>
  ruleName: string
  lifecycleLabel: string
}

interface CategoryDeltaRow {
  key: BreakdownKey
  label: string
  delta: number
  deltaText: string
  winnerLabel: string
}

interface DirectCostDeltaRow {
  key: DirectCostKey
  label: string
  aValue: number
  bValue: number
  delta: number
  deltaText: string
  deltaRateText: string
  winnerLabel: string
  direction: 'up' | 'down' | 'flat'
  arrow: string
}

const breakdownOrder: BreakdownKey[] = ['CAPEX', 'OPEX', 'M&R', 'RISK_COST', 'EOL']
const directCostOrder: DirectCostKey[] = ['labor', 'machine', 'material']
const breakdownLabelMap: Record<BreakdownKey, string> = {
  CAPEX: 'CAPEX',
  OPEX: 'OPEX',
  'M&R': 'M&R',
  RISK_COST: 'RISK',
  EOL: 'EOL',
}
const directCostLabelMap: Record<DirectCostKey, string> = {
  labor: '人员成本',
  machine: '设备成本',
  material: '材料成本',
}
const breakdownColorMap: Record<'A' | 'B', string> = {
  A: '#53d1ff',
  B: '#ff9d57',
}

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const promoting = ref(false)
const errorMessage = ref('')
const selectedSnapshotId = ref<number | null>(null)
const compareSnapshots = ref<CompareSnapshotViewModel[]>([])
const promotionResult = ref<PromoteSnapshotToVersionResponse | null>(null)
const compareChartRef = ref<HTMLElement | null>(null)

let compareChart: echarts.ECharts | null = null

const snapshotIds = computed(() => {
  const sid1 = Number(route.query.sid1)
  const sid2 = Number(route.query.sid2)
  if (!Number.isInteger(sid1) || !Number.isInteger(sid2) || sid1 <= 0 || sid2 <= 0 || sid1 === sid2) {
    return []
  }
  return [sid1, sid2]
})

const snapshotA = computed(() => compareSnapshots.value[0] ?? null)
const snapshotB = computed(() => compareSnapshots.value[1] ?? null)
const cheaperSnapshot = computed(() => {
  if (!snapshotA.value || !snapshotB.value) return null
  return snapshotA.value.totalCost <= snapshotB.value.totalCost ? snapshotA.value : snapshotB.value
})
const expensiveSnapshot = computed(() => {
  if (!snapshotA.value || !snapshotB.value) return null
  return snapshotA.value.totalCost > snapshotB.value.totalCost ? snapshotA.value : snapshotB.value
})
const costDelta = computed(() => {
  if (!snapshotA.value || !snapshotB.value) return 0
  return Math.abs(snapshotA.value.totalCost - snapshotB.value.totalCost)
})
const costDeltaRate = computed(() => {
  const base = expensiveSnapshot.value?.totalCost ?? 0
  return base > 0 ? costDelta.value / base : 0
})
const recommendationTag = computed(() => (cheaperSnapshot.value ? `建议采用方案 ${cheaperSnapshot.value.slot}` : '待判断'))
const recommendationText = computed(() => {
  if (!cheaperSnapshot.value || !expensiveSnapshot.value) return '待加载双方案数据'
  return `${cheaperSnapshot.value.slot} 相对 ${expensiveSnapshot.value.slot} 预计节约 ${formatWan(costDelta.value)}，降幅 ${formatPercent(costDeltaRate.value)}`
})
const rightCardTrend = computed(() => {
  if (!snapshotA.value || !snapshotB.value) return null

  return buildBaselineTrend(snapshotA.value.totalCost, snapshotB.value.totalCost)
})

const categoryDeltaRows = computed<CategoryDeltaRow[]>(() => {
  if (!snapshotA.value || !snapshotB.value) return []

  return breakdownOrder.map((key) => {
    const aValue = snapshotA.value?.breakdown[key] ?? 0
    const bValue = snapshotB.value?.breakdown[key] ?? 0
    const delta = Math.abs(aValue - bValue)
    const winner = aValue <= bValue ? snapshotA.value : snapshotB.value
    return {
      key,
      label: breakdownLabelMap[key],
      delta,
      deltaText: formatWan(delta),
      winnerLabel: `${winner.slot} 在 ${breakdownLabelMap[key]} 维度更优`,
    }
  }).sort((left, right) => right.delta - left.delta)
})

const directCostDeltaRows = computed<DirectCostDeltaRow[]>(() => {
  if (!snapshotA.value || !snapshotB.value) return []

  return directCostOrder.map((key) => {
    const aValue = snapshotA.value.directCosts[key] ?? 0
    const bValue = snapshotB.value.directCosts[key] ?? 0
    const trend = buildBaselineTrend(aValue, bValue)
    const delta = Math.abs(bValue - aValue)
    const winnerLabel = delta === 0
      ? '两案持平'
      : bValue < aValue
        ? '方案 B 更低'
        : '方案 A 更低'

    return {
      key,
      label: directCostLabelMap[key],
      aValue,
      bValue,
      delta,
      deltaText: formatWan(delta),
      deltaRateText: trend.text,
      winnerLabel,
      direction: trend.direction,
      arrow: trend.arrow,
    }
  })
})

const topDeltaCategoryLabel = computed(() => categoryDeltaRows.value[0]?.label || '--')
const selectedSnapshot = computed(() => compareSnapshots.value.find((item) => item.snapshot.id === selectedSnapshotId.value) ?? null)
const otherSnapshot = computed(() => compareSnapshots.value.find((item) => item.snapshot.id !== selectedSnapshotId.value) ?? null)

const decisionDescription = computed(() => {
  if (!selectedSnapshot.value || !otherSnapshot.value) {
    return '请选择待推优方案后生成版本说明。'
  }

  const selected = selectedSnapshot.value
  const other = otherSnapshot.value
  const totalGap = selected.totalCost - other.totalCost
  const preferredCategory = breakdownOrder
    .map((key) => ({
      key,
      label: breakdownLabelMap[key],
      advantage: other.breakdown[key] - selected.breakdown[key],
    }))
    .sort((left, right) => right.advantage - left.advantage)[0]

  if (totalGap <= 0) {
    return `经 A/B 对标，确认采用方案 ${selected.slot}（${selected.snapshot.snapshot_code} / ${selected.snapshot.snapshot_name}）进入正式版本。其 LCC 总成本现值为 ${formatWan(selected.totalCost)}，较方案 ${other.slot} 降低 ${formatWan(Math.abs(totalGap))}，降幅 ${formatPercent(Math.abs(totalGap) / Math.max(other.totalCost, 1))}；主要优势集中在 ${preferredCategory.label} 维度。`
  }

  if (preferredCategory.advantage > 0) {
    return `经管理层综合评估，确认将方案 ${selected.slot}（${selected.snapshot.snapshot_code} / ${selected.snapshot.snapshot_name}）推优为正式版本。该方案 LCC 总成本现值为 ${formatWan(selected.totalCost)}，虽较方案 ${other.slot} 高出 ${formatWan(Math.abs(totalGap))}，但在 ${preferredCategory.label} 维度仍保有 ${formatWan(preferredCategory.advantage)} 的结构性优势，符合当前工艺推进口径。`
  }

  return `经管理层综合评估，确认将方案 ${selected.slot}（${selected.snapshot.snapshot_code} / ${selected.snapshot.snapshot_name}）推优为正式版本。该方案 LCC 总成本现值为 ${formatWan(selected.totalCost)}，将作为当前阶段的正式版本基线继续推进。`
})

function toNumber(value: unknown): number {
  if (typeof value === 'number') return Number.isFinite(value) ? value : 0
  if (typeof value === 'string') {
    const parsed = Number(value)
    return Number.isFinite(parsed) ? parsed : 0
  }
  return 0
}

function formatWan(value: number): string {
  return `${(value / 10000).toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })} 万元`
}

function formatPercent(value: number): string {
  return `${(value * 100).toFixed(2)}%`
}

function buildBaselineTrend(base: number, current: number): { direction: 'up' | 'down' | 'flat'; arrow: string; text: string } {
  const delta = current - base
  if (Math.abs(delta) < 0.000001) {
    return { direction: 'flat', arrow: '→', text: '持平 0.00%' }
  }

  if (base <= 0) {
    return {
      direction: delta > 0 ? 'up' : 'down',
      arrow: delta > 0 ? '↑' : '↓',
      text: delta > 0 ? '新增 --' : '下降 --',
    }
  }

  const direction = delta > 0 ? 'up' : 'down'
  return {
    direction,
    arrow: delta > 0 ? '↑' : '↓',
    text: `${delta > 0 ? '上升' : '下降'} ${formatPercent(Math.abs(delta) / base)}`,
  }
}

function buildDirectCosts(costBreakdown?: StaticCostBreakdown | null): Record<DirectCostKey, number> {
  return {
    labor: toNumber(costBreakdown?.total_labor),
    machine: toNumber(costBreakdown?.total_machine),
    material: toNumber(costBreakdown?.total_material),
  }
}

function buildSnapshotViewModel(
  slot: 'A' | 'B',
  snapshot: ModelSnapshot,
  costBreakdown?: StaticCostBreakdown | null,
): CompareSnapshotViewModel {
  const simulation = snapshot.simulation_result
  const financialBaseline = simulation?.financial_baseline
  const lifecycleYears = Number(financialBaseline?.lifecycle_years)

  return {
    slot,
    snapshot,
    totalCost: toNumber(simulation?.lcc_total_cost),
    breakdown: {
      CAPEX: toNumber(simulation?.financial_breakdown?.CAPEX),
      OPEX: toNumber(simulation?.financial_breakdown?.OPEX),
      'M&R': toNumber(simulation?.financial_breakdown?.['M&R']),
      RISK_COST: toNumber(simulation?.financial_breakdown?.RISK_COST),
      EOL: toNumber(simulation?.financial_breakdown?.EOL),
    },
    directCosts: buildDirectCosts(costBreakdown),
    ruleName: financialBaseline?.rule_name || '未命名财务基准',
    lifecycleLabel: Number.isFinite(lifecycleYears) ? `${lifecycleYears} 年生命周期` : '未设置生命周期',
  }
}

async function loadCompareData() {
  if (snapshotIds.value.length !== 2) {
    errorMessage.value = 'URL 参数缺失或无效，无法发起双方案对比。'
    compareSnapshots.value = []
    return
  }

  loading.value = true
  errorMessage.value = ''
  promotionResult.value = null

  try {
    const [leftRes, rightRes, leftLedgerRes, rightLedgerRes] = await Promise.all([
      modelSnapshotApi.detail(snapshotIds.value[0]),
      modelSnapshotApi.detail(snapshotIds.value[1]),
      getStaticCostLedger(snapshotIds.value[0]).catch((error) => {
        console.warn('加载方案 A 静态成本台账失败:', error)
        return null
      }),
      getStaticCostLedger(snapshotIds.value[1]).catch((error) => {
        console.warn('加载方案 B 静态成本台账失败:', error)
        return null
      }),
    ])

    const snapshots = [leftRes.data, rightRes.data]
    const invalidSnapshot = snapshots.find((snapshot) => {
      const simulation = snapshot.simulation_result
      return (
        snapshot.status !== 'COMPLETED'
        || !simulation
        || simulation.simulation_type !== 'PROCESS_CHEMICAL'
      )
    })

    if (invalidSnapshot) {
      errorMessage.value = `快照 ${invalidSnapshot.snapshot_code} 不是已完成的化工 LCC 仿真结果。`
      compareSnapshots.value = []
      return
    }

    compareSnapshots.value = [
      buildSnapshotViewModel('A', snapshots[0], leftLedgerRes?.data?.cost_breakdown ?? null),
      buildSnapshotViewModel('B', snapshots[1], rightLedgerRes?.data?.cost_breakdown ?? null),
    ]
    selectedSnapshotId.value = cheaperSnapshot.value?.snapshot.id ?? compareSnapshots.value[0]?.snapshot.id ?? null

    await nextTick()
    renderCompareChart()
  } catch (error: any) {
    console.error('加载多方案对比失败:', error)
    errorMessage.value = error.response?.data?.message || '加载多方案对比数据失败'
    compareSnapshots.value = []
  } finally {
    loading.value = false
  }
}

function ensureChart(): echarts.ECharts | null {
  if (!compareChartRef.value) return null
  if (compareChart) return compareChart
  compareChart = echarts.init(compareChartRef.value)
  return compareChart
}

function renderCompareChart() {
  const chart = ensureChart()
  if (!chart || !snapshotA.value || !snapshotB.value) return

  const categories = breakdownOrder.map((key) => breakdownLabelMap[key])
  const aData = breakdownOrder.map((key) => Number((snapshotA.value?.breakdown[key] ?? 0) / 10000))
  const bData = breakdownOrder.map((key) => Number((snapshotB.value?.breakdown[key] ?? 0) / 10000))

  chart.setOption({
    backgroundColor: 'transparent',
    color: [breakdownColorMap.A, breakdownColorMap.B],
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: 'rgba(6, 16, 30, 0.96)',
      borderColor: 'rgba(255, 255, 255, 0.08)',
      textStyle: { color: '#ecf6ff' },
      formatter: (params: any[]) => {
        const title = params[0]?.axisValueLabel || ''
        const rows = params.map((item) => `${item.marker}${item.seriesName}：${Number(item.value).toFixed(2)} 万元`)
        return [title, ...rows].join('<br/>')
      },
    },
    grid: { left: 48, right: 18, top: 54, bottom: 36 },
    legend: {
      top: 4,
      textStyle: { color: '#9db6da' },
      data: ['方案 A', '方案 B'],
    },
    xAxis: {
      type: 'category',
      data: categories,
      axisLine: { lineStyle: { color: 'rgba(125, 152, 191, 0.28)' } },
      axisLabel: { color: '#9db6da' },
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#9db6da', formatter: (value: number) => `${value.toFixed(0)}w` },
      splitLine: { lineStyle: { color: 'rgba(125, 152, 191, 0.16)' } },
      name: '万元',
      nameTextStyle: { color: '#6f8aad' },
    },
    series: [
      {
        name: '方案 A',
        type: 'bar',
        barMaxWidth: 26,
        itemStyle: { borderRadius: [10, 10, 0, 0] },
        data: aData,
      },
      {
        name: '方案 B',
        type: 'bar',
        barMaxWidth: 26,
        itemStyle: { borderRadius: [10, 10, 0, 0] },
        data: bData,
      },
    ],
  })
}

function resizeChart() {
  compareChart?.resize()
}

async function handleSelect(snapshotId: number) {
  if (promoting.value) {
    return
  }

  selectedSnapshotId.value = snapshotId
  promotionResult.value = null
  await nextTick()

  if (!selectedSnapshot.value) {
    return
  }

  try {
    await ElMessageBox.confirm(
      `确认将方案 ${selectedSnapshot.value.slot}（${selectedSnapshot.value.snapshot.snapshot_code} / ${selectedSnapshot.value.snapshot.snapshot_name}）推优为新版本吗？\n\n${decisionDescription.value}`,
      '确认推优',
      {
        confirmButtonText: '确认生成版本',
        cancelButtonText: '取消',
        type: 'warning',
      },
    )
  } catch {
    return
  }

  await handlePromote()
}

async function handlePromote() {
  if (promoting.value) {
    return
  }

  if (!selectedSnapshot.value) {
    ElMessage.warning('请先选择待推优方案')
    return
  }

  promoting.value = true
  try {
    const res = await modelSnapshotApi.promoteToVersion(
      selectedSnapshot.value.snapshot.id,
      {
      description: decisionDescription.value,
      },
    )
    promotionResult.value = res.data
    ElMessage.success(res.data.message)
  } catch (error: any) {
    console.error('推优正式版本失败:', error)
    ElMessage.error(error.response?.data?.message || '推优正式版本失败')
  } finally {
    promoting.value = false
  }
}

function handleBack() {
  router.push('/costing/snapshot-center')
}

watch(() => [route.query.sid1, route.query.sid2], () => {
  void loadCompareData()
})

onMounted(() => {
  void loadCompareData()
  window.addEventListener('resize', resizeChart)
})

onUnmounted(() => {
  window.removeEventListener('resize', resizeChart)
  compareChart?.dispose()
  compareChart = null
})
</script>

<style scoped>
.lcc-compare-view {
  min-height: 100%;
  padding: 18px;
  background:
    radial-gradient(circle at top left, rgba(34, 85, 143, 0.28), transparent 28%),
    radial-gradient(circle at top right, rgba(255, 133, 64, 0.18), transparent 22%),
    linear-gradient(180deg, #08111f 0%, #07101b 42%, #060c16 100%);
}

.compare-shell {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.compare-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 18px;
  padding: 20px 24px;
  border-radius: 28px;
  background: linear-gradient(135deg, rgba(11, 26, 45, 0.96), rgba(8, 17, 30, 0.92));
  box-shadow: inset 0 0 0 1px rgba(113, 141, 181, 0.1);
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.back-button {
  align-self: flex-start;
  color: #a9c2e7;
}

.title-block h1 {
  margin: 6px 0 8px;
  color: #f3f7fd;
  font-size: 32px;
  line-height: 1.15;
  font-family: Bahnschrift, "Segoe UI", sans-serif;
  letter-spacing: 0.03em;
}

.title-block p {
  margin: 0;
  color: #87a1c6;
  font-size: 14px;
}

.eyebrow {
  color: #63cfff;
  font-size: 12px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

.header-right {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.summary-card {
  padding: 22px;
  border-radius: 24px;
  color: #eff5ff;
  background: linear-gradient(180deg, rgba(12, 25, 43, 0.94), rgba(7, 14, 25, 0.9));
  box-shadow: inset 0 0 0 1px rgba(113, 141, 181, 0.1);
}

.scheme-a {
  box-shadow: inset 0 0 0 1px rgba(83, 209, 255, 0.18), 0 18px 42px rgba(0, 0, 0, 0.18);
}

.scheme-b {
  box-shadow: inset 0 0 0 1px rgba(255, 157, 87, 0.18), 0 18px 42px rgba(0, 0, 0, 0.18);
}

.scheme-delta {
  box-shadow: inset 0 0 0 1px rgba(113, 255, 181, 0.14), 0 18px 42px rgba(0, 0, 0, 0.18);
}

.summary-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 20px;
  font-size: 12px;
  color: #8fa8cb;
}

.summary-head-side {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
}

.summary-badge {
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.summary-code {
  color: #6f8aad;
}

.summary-trend {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 600;
}

.summary-trend.baseline,
.summary-trend.is-flat {
  color: #8fa8cb;
}

.summary-trend.is-down {
  color: #67e0a5;
}

.summary-trend.is-up {
  color: #ff9d57;
}

.summary-trend-arrow {
  font-size: 14px;
  line-height: 1;
}

.summary-value {
  font-size: 34px;
  line-height: 1.1;
  font-weight: 700;
  font-family: Bahnschrift, "Segoe UI", sans-serif;
}

.summary-value.accent {
  color: #ffcf70;
}

.summary-title {
  margin-top: 10px;
  font-size: 18px;
  color: #f2f6ff;
}

.summary-meta {
  margin-top: 8px;
  color: #88a1c6;
  font-size: 13px;
  line-height: 1.6;
}

.content-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.6fr) minmax(320px, 0.9fr);
  gap: 16px;
}

.panel {
  border-radius: 24px;
  padding: 20px 22px;
  background: linear-gradient(180deg, rgba(10, 22, 38, 0.96), rgba(7, 13, 24, 0.92));
  box-shadow: inset 0 0 0 1px rgba(113, 141, 181, 0.1);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 16px;
}

.panel-header h3 {
  margin: 0 0 6px;
  color: #f2f7ff;
  font-size: 20px;
}

.panel-header p,
.panel-note,
.decision-status {
  margin: 0;
  color: #7f99be;
  font-size: 13px;
}

.chart-canvas {
  height: 360px;
}

.resource-delta-card {
  margin-top: 20px;
  padding: 18px;
  border-radius: 20px;
  background: rgba(9, 19, 33, 0.82);
  box-shadow: inset 0 0 0 1px rgba(113, 141, 181, 0.08);
}

.resource-delta-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 14px;
}

.resource-delta-header h4 {
  margin: 0 0 6px;
  color: #eff5ff;
  font-size: 18px;
}

.resource-delta-header p {
  margin: 0;
  color: #7f99be;
  font-size: 13px;
}

.resource-delta-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.resource-delta-item {
  padding: 14px 16px;
  border-radius: 16px;
  background: rgba(14, 28, 47, 0.88);
  box-shadow: inset 0 0 0 1px rgba(113, 141, 181, 0.08);
}

.resource-delta-top,
.resource-delta-values {
  display: flex;
  justify-content: space-between;
  gap: 10px;
}

.resource-delta-label {
  color: #eef5ff;
  font-size: 14px;
  font-weight: 600;
}

.resource-delta-trend {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 600;
}

.resource-delta-trend.is-flat {
  color: #8fa8cb;
}

.resource-delta-trend.is-down {
  color: #67e0a5;
}

.resource-delta-trend.is-up {
  color: #ff9d57;
}

.resource-delta-arrow {
  font-size: 14px;
}

.resource-delta-values {
  margin-top: 14px;
  color: #b8cae4;
  font-size: 13px;
}

.resource-delta-footer {
  margin-top: 10px;
  color: #7f99be;
  font-size: 12px;
  line-height: 1.6;
}

.insight-kpis {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
  margin-bottom: 18px;
}

.kpi-block {
  padding: 14px 16px;
  border-radius: 16px;
  background: rgba(15, 30, 51, 0.72);
  box-shadow: inset 0 0 0 1px rgba(113, 141, 181, 0.08);
}

.kpi-label {
  display: block;
  margin-bottom: 8px;
  color: #7f99be;
  font-size: 12px;
}

.kpi-block strong {
  color: #f4f8ff;
  font-size: 20px;
}

.delta-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.delta-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  padding: 12px 14px;
  border-radius: 16px;
  background: rgba(10, 21, 37, 0.78);
}

.delta-label {
  color: #e7efff;
  font-size: 14px;
}

.delta-helper {
  margin-top: 4px;
  color: #6f8aad;
  font-size: 12px;
}

.delta-value {
  color: #ffcf70;
  font-size: 14px;
  font-weight: 700;
}

.decision-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.decision-header {
  margin-bottom: 0;
}

.decision-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.decision-card {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 18px;
  border: none;
  border-radius: 20px;
  text-align: left;
  color: #eff6ff;
  background: rgba(11, 24, 42, 0.88);
  box-shadow: inset 0 0 0 1px rgba(113, 141, 181, 0.1);
  cursor: pointer;
  transition: transform 0.18s ease, box-shadow 0.18s ease, background 0.18s ease;
}

.decision-card:hover {
  transform: translateY(-2px);
}

.decision-card.selected {
  background: rgba(17, 40, 69, 0.96);
  box-shadow: inset 0 0 0 1px rgba(98, 207, 255, 0.42), 0 14px 34px rgba(0, 0, 0, 0.2);
}

.decision-card.recommended {
  box-shadow: inset 0 0 0 1px rgba(102, 230, 173, 0.28);
}

.decision-card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  color: #a8bfdc;
}

.decision-card strong {
  font-size: 26px;
  font-family: Bahnschrift, "Segoe UI", sans-serif;
}

.decision-card span,
.decision-card small {
  display: block;
}

.decision-card small {
  color: #6f8aad;
}

.decision-output {
  padding: 18px;
  border-radius: 20px;
  background: rgba(10, 19, 34, 0.88);
  box-shadow: inset 0 0 0 1px rgba(113, 141, 181, 0.08);
}

.decision-copy-title {
  margin-bottom: 10px;
  color: #8ba5c9;
  font-size: 12px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.decision-copy {
  color: #eef5ff;
  line-height: 1.8;
  font-size: 14px;
}

.promotion-result {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 16px;
  border-radius: 16px;
  color: #d9ffe9;
  background: rgba(14, 64, 44, 0.42);
  box-shadow: inset 0 0 0 1px rgba(86, 206, 146, 0.18);
}

.decision-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.state-shell {
  min-height: 72vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 18px;
}

.state-shell :deep(.el-empty__description p) {
  color: #8ba5c9;
}

@media (max-width: 1200px) {
  .summary-grid,
  .content-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .lcc-compare-view {
    padding: 12px;
  }

  .compare-header,
  .panel,
  .summary-card {
    padding: 16px;
    border-radius: 20px;
  }

  .header-right,
  .decision-grid,
  .decision-actions,
  .promotion-result,
  .resource-delta-header,
  .resource-delta-values {
    flex-direction: column;
  }

  .decision-grid {
    grid-template-columns: 1fr;
  }

  .resource-delta-grid {
    grid-template-columns: 1fr;
  }

  .title-block h1 {
    font-size: 24px;
  }

  .summary-value {
    font-size: 28px;
  }

  .chart-canvas {
    height: 320px;
  }
}
</style>
