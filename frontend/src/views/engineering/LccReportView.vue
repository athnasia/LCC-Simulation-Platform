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
            <h1>
              {{ snapshotNameDisplay }}
              <span class="snapshot-code">报告编号：{{ snapshotCodeDisplay }}</span>
            </h1>
            <div v-if="isChemicalSimulation" class="title-subline">
              项目名称：{{ snapshotNameDisplay }} | LCC 全生命周期成本折现推演报告
            </div>
            <div v-else class="title-subline">工序推演 / 虚拟时间轴成本对标</div>
          </div>
        </div>
        <div
          class="header-right"
          style="
            display: flex;
            flex-direction: column;
            align-items: flex-end;
            gap: 12px;
            z-index: 10;
          "
        >
          <el-collapse class="data-specs-collapse" style="width: 320px">
            <el-collapse-item name="1">
              <template #title>
                <div class="collapse-title">📑 数据口径说明</div>
              </template>
              <ul class="specs-list">
                <li>折现率：8%</li>
                <li>计算周期：15 年</li>
                <li>LCOE 计算逻辑：全生命周期总成本 ÷ 总发电量</li>
                <li>风险成本：按当年 OPEX 的 0.75% 计提</li>
                <li>能耗数据：基于满负荷运行工况理论推演</li>
              </ul>
            </el-collapse-item>
          </el-collapse>
        </div>
      </div>

      <template v-if="isChemicalSimulation">
        <div class="conclusion-panel">
          <div class="conclusion-title">仿真核心结论</div>
          <div class="conclusion-text">
            本项目全生命周期度电成本 (LCOE) 为
            <span class="highlight">{{
              chemicalEnergyAnalysis?.weighted_price || "--"
            }}</span>
            元/度，总成本净现值
            <span class="highlight">{{ formatCurrency(dynamicTotalCost) }}</span
            >。运营成本占比超过 50%，建议重点优化能源效率与原材料采购成本。
          </div>
        </div>

        <el-row :gutter="24" class="hero-metrics chemical-metrics">
          <el-col
            v-for="card in financialCards"
            :key="card.key"
            :xs="24"
            :sm="12"
            class="col-lg-5"
          >
            <div class="metric-card chemical-card" :class="card.cardClass">
              <div class="metric-label">
                {{ card.label }}
                <el-tooltip
                  v-if="card.key === 'EOL' && card.rawValue < 0"
                  content="处置成本大于残值回收，为净支出项"
                  placement="top"
                >
                  <el-icon class="warn-icon"><Warning /></el-icon>
                </el-tooltip>
              </div>
              <div class="metric-value">{{ card.value }}</div>
              <div class="metric-subtitle">= {{ card.subtitle }}</div>
            </div>
          </el-col>
        </el-row>

        <el-row :gutter="24" class="energy-metrics" v-if="chemicalEnergyAnalysis">
          <el-col :xs="24" :md="6">
            <div class="metric-card energy-card energy-lcoe">
              <div class="metric-label">
                综合度电价格 (LCOE)
                <el-tooltip
                  :content="`基于 ${chemicalEnergyAnalysis.rate_code} 加权折算 (x ${chemicalEnergyAnalysis.weighted_multiplier})`"
                  placement="top"
                >
                  <el-icon class="info-icon"><InfoFilled /></el-icon>
                </el-tooltip>
              </div>
              <div class="metric-value">
                {{ chemicalEnergyAnalysis.weighted_price }}
                <span class="unit-text">元/度</span>
              </div>
            </div>
          </el-col>
          <el-col :xs="24" :md="6">
            <div class="metric-card energy-card">
              <div class="metric-label">工序单组推演能耗</div>
              <div class="metric-value">
                {{ Number(chemicalEnergyAnalysis.energy_kwh_per_run).toFixed(2) }}
                <span class="unit-text">kWh</span>
              </div>
              <div class="metric-subtitle">= 全线受控物理设备理论单次功耗合计</div>
            </div>
          </el-col>
          <el-col :xs="24" :md="6">
            <div class="metric-card energy-card">
              <div class="metric-label">年化总电网采购预算</div>
              <div class="metric-value">
                {{ chemicalEnergyAnalysis.annual_energy_cost }}
              </div>
              <div class="metric-subtitle">= 年满负荷折算电费（已融入LCC OPEX）</div>
            </div>
          </el-col>
          <el-col :xs="24" :md="6">
            <div class="metric-card energy-card">
              <div class="metric-label">常态非能源运营支出</div>
              <div class="metric-value">
                {{ chemicalEnergyAnalysis.annual_regular_opex }}
              </div>
              <div class="metric-subtitle">= 含生产原料与全职人员薪酬</div>
            </div>
          </el-col>
        </el-row>

        <el-row :gutter="24" class="charts-grid chemical-grid">
          <el-col :xs="24" :lg="10">
            <div class="chart-card chemical-panel">
              <div
                class="chart-header"
                style="
                  display: flex;
                  justify-content: space-between;
                  align-items: flex-start;
                "
              >
                <div>
                  <h3>五维成本结构环形图</h3>
                  <span>资本投入、运营消耗、维保、风险与处置残值占比</span>
                </div>
                <div style="text-align: right">
                  <div style="color: #94a3b8; font-size: 14px; margin-bottom: 4px">
                    全生命周期成本净现值
                  </div>
                  <div style="color: #f8fafc; font-size: 28px; font-weight: 700">
                    ¥
                    {{
                      dynamicTotalCost.toLocaleString("zh-CN", {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2,
                      })
                    }}
                  </div>
                </div>
              </div>
              <div ref="chemicalDonutChartRef" class="chart-canvas"></div>
              <div class="chart-insight">
                成本结构分析：运营成本 (OPEX) 占比最高，为项目成本控制核心；初始投资
                (CAPEX) 占比次之；维保与风险成本合计占比不足 5%，整体成本结构健康。
              </div>
            </div>
          </el-col>
          <el-col :xs="24" :lg="14">
            <div class="chart-card chemical-panel">
              <div class="chart-header">
                <h3>全生命周期成本现金流折现分布</h3>
                <span>Year 0 CAPEX 起投，Year 1-N 折现 OPEX / M&amp;R / Risk / EOL</span>
              </div>
              <div
                ref="chemicalCashflowChartRef"
                class="chart-canvas chart-canvas-wide"
              ></div>
              <div class="chart-insight">
                现金流分布：项目成本集中在建设期 (Year
                0)，运营期成本逐年平稳递减，处置期产生净支出。
              </div>
            </div>
          </el-col>
        </el-row>

        <div class="audit-card chemical-panel">
          <div class="chart-header">
            <h3>宏观审计表</h3>
            <span>逐年现值拆解与累计净现值审计</span>
          </div>
          <el-table :data="chemicalAuditRows" border class="audit-table chemical-table">
            <el-table-column
              prop="yearLabel"
              label="项目周期（年）"
              width="130"
              fixed="left"
            />
            <el-table-column
              prop="pvOpex"
              label="运营成本现值(OPEX)"
              min-width="160"
              align="right"
            />
            <el-table-column
              prop="pvMaintenance"
              label="维保成本现值(M&R)"
              min-width="160"
              align="right"
            />
            <el-table-column
              prop="pvRisk"
              label="风险拨备现值(Risk Cost)"
              min-width="160"
              align="right"
            />
            <el-table-column
              prop="pvEol"
              label="期末处置现值(EOL)"
              min-width="160"
              align="right"
            />
            <el-table-column
              prop="yearTotal"
              label="年度成本现值合计(Total)"
              min-width="180"
              align="right"
            />
            <el-table-column
              prop="cumulativeNpv"
              label="累计成本净现值(NPV)"
              min-width="180"
              align="right"
              fixed="right"
            >
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
              <div class="metric-value emphasis">
                {{ formatCurrency(dynamicTotalCost) }}
              </div>
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
              <div class="metric-value compact">
                {{ peakHitCount }} / {{ virtualCycleDisplay }}
              </div>
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
            <el-table-column
              prop="process_name"
              label="工序名称"
              min-width="160"
              fixed="left"
            />
            <el-table-column prop="process_type" label="工艺类型" width="120">
              <template #default="{ row }">
                <el-tag
                  :type="row.process_type === 'OUTSOURCED' ? 'danger' : 'primary'"
                  effect="dark"
                >
                  {{ row.process_type === "OUTSOURCED" ? "外协" : "自制" }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="start_time_label" label="开始时间" width="180" />
            <el-table-column prop="end_time_label" label="结束时间" width="180" />
            <el-table-column prop="machine_cost" label="机器费" width="120" align="right">
              <template #default="{ row }">{{
                formatCurrency(row.machine_cost)
              }}</template>
            </el-table-column>
            <el-table-column prop="labor_cost" label="人工费" width="120" align="right">
              <template #default="{ row }">{{ formatCurrency(row.labor_cost) }}</template>
            </el-table-column>
            <el-table-column prop="energy_cost" label="电费" width="120" align="right">
              <template #default="{ row }">{{
                formatCurrency(row.energy_cost)
              }}</template>
            </el-table-column>
            <el-table-column
              prop="material_cost"
              label="材料费"
              width="120"
              align="right"
            >
              <template #default="{ row }">{{
                formatCurrency(row.material_cost)
              }}</template>
            </el-table-column>
            <el-table-column prop="total_cost" label="工序总计" width="140" align="right">
              <template #default="{ row }">
                <span class="total-cell">{{ formatCurrency(row.total_cost) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="异常备注" min-width="180" fixed="right">
              <template #default="{ row }">
                <el-tag v-if="row.hit_peak" type="danger" effect="dark"
                  >峰值电价命中</el-tag
                >
                <el-tag v-else-if="row.hit_valley" type="success" effect="dark"
                  >谷电窗口</el-tag
                >
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
import { ArrowLeft, Bottom, Top, Warning, InfoFilled } from '@element-plus/icons-vue'
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

interface ChemicalEnergyAnalysis {
  rate_code: string
  base_price: string
  weighted_multiplier: string
  weighted_price: string
  energy_kwh_per_run: string
  annual_energy_kwh: string
  annual_energy_cost: string
  annual_regular_opex: string
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

const chemicalEnergyAnalysis = ref<ChemicalEnergyAnalysis | null>(null)

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
      subtitle: '含腐蚀老化附加成本',
      value: formatCurrency(financialBreakdown.value['M&R']),
      rawValue: financialBreakdown.value['M&R'],
      displayValue: Math.abs(financialBreakdown.value['M&R']),
      cardClass: 'financial-mr',
    },
    {
      key: 'RISK_COST',
      label: 'RISK COST (风险拨备现值)',
      subtitle: '按OPEX比例计提拨备',
      value: formatCurrency(financialBreakdown.value.RISK_COST),
      rawValue: financialBreakdown.value.RISK_COST,
      displayValue: Math.abs(financialBreakdown.value.RISK_COST),
      cardClass: 'financial-risk',
    },
    {
      key: 'EOL',
      label: 'EOL (期末处置与残值)',
      subtitle: '残值回收-拆除处置成本',
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

  chemicalEnergyAnalysis.value = simulation.chemical_energy_analysis || null
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
      axisLine: { lineStyle: { color: '#334155' } },
      axisLabel: {
        color: '#94A3B8',
        interval: (index: number, value: string) => {
          if (value === 'Year 0' || value === 'Year 5' || value === 'Year 10' || value === 'Year 15') return true
          return false
        }
      },
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      axisLabel: {
        color: '#94A3B8',
        formatter: (value: number) => `¥${(value / 10000).toFixed(0)}w`,
      },
      splitLine: { lineStyle: { color: gridLineColor } },
      name: '现值金额',
      nameTextStyle: { color: '#94A3B8', padding: [0, 0, 8, 0] },
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
  min-height: calc(100vh - 64px);
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
  color: #f8fafc;
  padding: 32px;
  font-family: "Inter", "Noto Sans SC", sans-serif;
  position: relative;
}

.lcc-report-view::before {
  content: "";
  position: absolute;
  inset: 0;
  background-image: linear-gradient(rgba(71, 85, 105, 0.1) 1px, transparent 1px),
    linear-gradient(90deg, rgba(71, 85, 105, 0.1) 1px, transparent 1px);
  background-size: 40px 40px;
  pointer-events: none;
}

.report-shell {
  max-width: 1600px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 32px;
  position: relative;
  z-index: 1;
}

.report-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.back-button {
  width: fit-content;
  color: #94a3b8;
}

.back-button:hover {
  color: #f8fafc;
}

.title-block h1 {
  margin: 0 0 8px 0;
  font-size: 28px;
  font-weight: 700;
  color: #f8fafc;
  display: flex;
  align-items: center;
  gap: 16px;
}

.snapshot-code {
  font-size: 14px;
  font-weight: 400;
  color: #94a3b8;
  padding: 4px 12px;
  background: rgba(51, 65, 85, 0.4);
  border-radius: 4px;
}

.title-subline {
  color: #94a3b8;
  font-size: 14px;
}

.conclusion-panel {
  background: rgba(30, 41, 59, 0.8);
  border: 1px solid #334155;
  border-radius: 8px;
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.conclusion-title {
  font-size: 16px;
  font-weight: 600;
  color: #10b981;
}

.conclusion-text {
  font-size: 14px;
  line-height: 1.6;
  color: #f8fafc;
}

.conclusion-text .highlight {
  font-weight: 700;
  color: #3b82f6;
}

.hero-metrics {
  margin-top: 0;
}

.metric-card {
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 8px;
  padding: 24px;
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.financial-capex {
  border-top: 2px solid #3b82f6;
}
.financial-opex {
  border-top: 2px solid #10b981;
}
.financial-mr {
  border-top: 2px solid #f59e0b;
}
.financial-risk {
  border-top: 2px solid #8b5cf6;
}
.financial-eol {
  border-top: 2px solid #a78bfa;
}

.metric-label {
  color: #94a3b8;
  font-size: 16px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 6px;
}

.warn-icon {
  color: #f59e0b;
  font-size: 16px;
  cursor: help;
}

.info-icon {
  color: #3b82f6;
  font-size: 16px;
  cursor: help;
}

.metric-value {
  color: #f8fafc;
  font-size: 28px;
  font-weight: 700;
  line-height: 1.2;
}

.metric-subtitle {
  color: #64748b;
  font-size: 12px;
}

.energy-metrics {
  margin-bottom: 0;
  display: flex;
  align-items: stretch;
  flex-wrap: wrap; /* 防止小屏幕下挤压 */
}

.energy-card {
  border-top: none;
  justify-content: center;
  height: 100%; /* 添加这行 */
  box-sizing: border-box; /* 添加这行 */
}

.energy-lcoe {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.15) 0%, #1e293b 100%);
  border: 1px solid rgba(59, 130, 246, 0.3);
}

.energy-lcoe .metric-value {
  font-size: 40px;
  color: #3b82f6;
}

.unit-text {
  font-size: 16px;
  font-weight: 400;
  color: #94a3b8;
  margin-left: 4px;
}

.mt-24 {
  margin-top: 24px;
}

.chart-card,
.audit-card {
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 8px;
  padding: 24px;
}

.chart-header {
  margin-bottom: 24px;
}

.chart-header h3 {
  margin: 0 0 4px 0;
  font-size: 20px;
  font-weight: 600;
  color: #f8fafc;
}

.chart-header span {
  font-size: 14px;
  color: #94a3b8;
}

.chart-canvas {
  height: 320px;
  width: 100%;
}

.chart-canvas-wide {
  height: 320px;
}

.chart-insight {
  margin-top: 16px;
  padding: 12px 16px;
  background: rgba(15, 23, 42, 0.5);
  border-radius: 4px;
  font-size: 13px;
  color: #94a3b8;
  line-height: 1.5;
}

.audit-table {
  --el-table-border-color: #334155;
  --el-table-header-bg-color: rgba(15, 23, 42, 0.8);
  --el-table-header-text-color: #f8fafc;
  --el-table-tr-bg-color: #1e293b;
  --el-table-row-hover-bg-color: rgba(51, 65, 85, 0.5);
  --el-table-text-color: #f8fafc;
  border-radius: 4px;
}

.el-table--striped .el-table__body tr.el-table__row--striped td.el-table__cell {
  background: rgba(15, 23, 42, 0.3);
}

.total-cell {
  color: #3b82f6;
  font-weight: 700;
}

.data-specs-collapse {
  --el-collapse-border-color: #334155;
  --el-collapse-header-bg-color: #1e293b;
  --el-collapse-header-text-color: #f8fafc;
  --el-collapse-content-bg-color: #1e293b;
  --el-collapse-content-text-color: #94a3b8;
  border: 1px solid #334155;
  border-radius: 8px;
  overflow: hidden;
}

.collapse-title {
  font-size: 16px;
  font-weight: 600;
  padding-left: 16px;
}

.specs-list {
  padding: 0 24px 16px 40px;
  margin: 0;
  line-height: 2;
  font-size: 13px;
}

@media (min-width: 1200px) {
  .col-lg-5 {
    max-width: 20%;
    flex: 0 0 20%;
  }
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 60vh;
  gap: 24px;
}
</style>
