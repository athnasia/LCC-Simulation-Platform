<template>
  <div class="dashboard-screen">
    <div class="screen-backdrop"></div>

    <header class="top-bar">
      <div class="title-block">
        <span class="eyebrow">LCC PANORAMIC SIMULATION / EXECUTIVE COMMAND</span>
        <h1>LCC 全景仿真与降本决策大屏</h1>
        <p>聚焦全局生命周期成本基底、项目 A/B 降本战果与未来 15 年折现压力带。</p>
      </div>
      <div class="time-chip">
        <span class="time-chip__label">数据截面</span>
        <strong>{{ boardMeta.snapshotDate }}</strong>
      </div>
    </header>

    <section class="kpi-grid">
      <article
        v-for="item in kpiCards"
        :key="item.label"
        class="kpi-card"
        :class="item.tone"
      >
        <div class="kpi-card__glow"></div>
        <div class="kpi-card__header">
          <span>{{ item.label }}</span>
          <small>{{ item.subLabel }}</small>
        </div>
        <div class="kpi-card__value">{{ item.value }}</div>
        <div class="kpi-card__footer">{{ item.footer }}</div>
      </article>
    </section>

    <section class="main-grid">
      <div class="left-column">
        <article class="panel-card stats-card">
          <div class="panel-head">
            <div>
              <span class="panel-title">基础要素数字化盘点</span>
              <p class="panel-subtitle">人员 / 设备 / 材料 / 工艺 四大字典条目厚度</p>
            </div>
            <span class="panel-tag">模块 A</span>
          </div>
          <div ref="assetChartRef" class="chart-block chart-block--medium"></div>
          <div class="mini-stat-grid">
            <div v-for="item in assetInventory" :key="item.name" class="mini-stat-card">
              <span class="mini-stat-card__label">{{ item.name }}</span>
              <strong>{{ formatCount(item.value) }}</strong>
              <small>{{ item.note }}</small>
            </div>
          </div>
        </article>

        <article class="panel-card donut-card">
          <div class="panel-head">
            <div>
              <span class="panel-title">全局五维成本结构</span>
              <p class="panel-subtitle">定稿方案 CAPEX / OPEX / M&amp;R / RISK / EOL 占比</p>
            </div>
            <span class="panel-tag">模块 B</span>
          </div>
          <div ref="structureChartRef" class="chart-block chart-block--large"></div>
        </article>
      </div>

      <div class="center-column">
        <article class="panel-card battle-card">
          <div class="panel-head panel-head--battle">
            <div>
              <span class="panel-title">A/B 方案降本对标</span>
              <p class="panel-subtitle">当前焦点项目 {{ focusProject.name }} 的五维成本结构差异</p>
            </div>
            <div class="panel-note-group">
              <span class="panel-note">模块 C</span>
              <span class="panel-note panel-note--accent">单位：万元</span>
            </div>
          </div>

          <div class="battle-highlight">
            <div class="battle-highlight__label">当前项目预计降本差额</div>
            <div class="battle-highlight__value">{{ focusProject.savingDisplay }}</div>
            <div class="battle-highlight__footer">
              推荐采用 <strong>{{ focusProject.recommendedPlan }}</strong>
              <span>{{ focusProject.recommendationReason }}</span>
            </div>
          </div>

          <div ref="compareChartRef" class="chart-block chart-block--hero"></div>

          <div class="scheme-summary-grid">
            <div v-for="plan in focusProject.plans" :key="plan.name" class="scheme-summary-card">
              <div class="scheme-summary-card__header">
                <span>{{ plan.name }}</span>
                <small>{{ plan.badge }}</small>
              </div>
              <strong>{{ plan.total }}</strong>
              <p>{{ plan.summary }}</p>
            </div>
          </div>
        </article>
      </div>

      <div class="right-column">
        <article class="panel-card ranking-card">
          <div class="panel-head">
            <div>
              <span class="panel-title">降本战果排行榜</span>
              <p class="panel-subtitle">核心项目降本金额 TOP 5</p>
            </div>
            <span class="panel-tag">模块 D</span>
          </div>

          <el-table
            :data="rankingRows"
            height="260"
            class="ranking-table"
            :header-cell-style="headerCellStyle"
            :cell-style="cellStyle"
          >
            <el-table-column type="index" label="#" width="56" />
            <el-table-column prop="projectName" label="项目名称" min-width="150" show-overflow-tooltip />
            <el-table-column prop="winner" label="胜出方案" width="110" />
            <el-table-column prop="saving" label="降本金额" width="120" align="right" />
          </el-table>
        </article>

        <article class="panel-card trend-card">
          <div class="panel-head">
            <div>
              <span class="panel-title">全局现金流折现预测</span>
              <p class="panel-subtitle">Year 0 - Year 15 CAPEX/OPEX/RISK 折现分布</p>
            </div>
            <span class="panel-tag">模块 E</span>
          </div>
          <div ref="cashflowChartRef" class="chart-block chart-block--medium"></div>
        </article>

        <article class="panel-card ai-wall-card">
          <div class="panel-head">
            <div>
              <span class="panel-title">AI 决策建议墙</span>
              <p class="panel-subtitle">最新版本推优建议与风险播报</p>
            </div>
            <span class="panel-tag">模块 F</span>
          </div>

          <div class="ai-wall-list">
            <div v-for="item in aiAdviceList" :key="item.id" class="ai-wall-item">
              <div class="ai-wall-item__dot"></div>
              <div class="ai-wall-item__content">
                <div class="ai-wall-item__meta">
                  <span>{{ item.project }}</span>
                  <small>{{ item.time }}</small>
                </div>
                <p>{{ item.message }}</p>
              </div>
            </div>
          </div>
        </article>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import type { CSSProperties } from 'vue'
import * as echarts from 'echarts'

type CostDimensionKey = 'CAPEX' | 'OPEX' | 'M&R' | 'RISK' | 'EOL'

interface AssetInventoryItem {
  name: string
  value: number
  note: string
}

interface KpiCard {
  label: string
  subLabel: string
  value: string
  footer: string
  tone: 'core' | 'blue' | 'green' | 'orange'
}

interface RankingRow {
  projectName: string
  winner: string
  saving: string
}

interface AdviceItem {
  id: number
  project: string
  time: string
  message: string
}

interface SchemePlanSummary {
  name: string
  badge: string
  total: string
  summary: string
}

const boardMeta = {
  snapshotDate: '2026-04-25 09:30',
}

const assetInventory: AssetInventoryItem[] = [
  { name: '人员', value: 248, note: '含工种 / 等级费率矩阵' },
  { name: '设备', value: 186, note: '含能耗系数与折旧费率' },
  { name: '材料', value: 1426, note: '含计价单位与换算映射' },
  { name: '工艺', value: 372, note: '已挂载机 / 人 / 材 / 能' },
]

const costStructure = [
  { name: 'CAPEX', value: 2680, color: '#38bdf8' },
  { name: 'OPEX', value: 3310, color: '#10b981' },
  { name: 'M&R', value: 980, color: '#f59e0b' },
  { name: 'RISK', value: 620, color: '#fb7185' },
  { name: 'EOL', value: 340, color: '#818cf8' },
]

const focusProject = {
  name: '乙烯裂解换热站改造',
  savingDisplay: '5.55 万元',
  recommendedPlan: '方案 B',
  recommendationReason: '主要优势集中在 OPEX 与 M&R 维度，长期折现压力更低。',
  plans: [
    {
      name: '方案 A',
      badge: '基准版',
      total: '128.35 万元',
      summary: '设备一次性投入较低，但运行能耗与维护支出偏高。',
    },
    {
      name: '方案 B',
      badge: '推荐版',
      total: '122.80 万元',
      summary: '初始 CAPEX 略增，换来更稳的 OPEX 与更低故障风险。',
    },
  ] as SchemePlanSummary[],
  dimensions: {
    A: { CAPEX: 32.8, OPEX: 41.6, 'M&R': 19.5, RISK: 21.4, EOL: 13.05 },
    B: { CAPEX: 36.2, OPEX: 34.1, 'M&R': 15.2, RISK: 18.0, EOL: 19.3 },
  } satisfies Record<'A' | 'B', Record<CostDimensionKey, number>>,
}

const rankingRows: RankingRow[] = [
  { projectName: '乙烯裂解换热站改造', winner: '方案 B', saving: '5.55 万' },
  { projectName: '合成氨蒸汽回收升级', winner: '方案 C', saving: '4.86 万' },
  { projectName: '聚合反应釜保温重构', winner: '方案 B', saving: '4.11 万' },
  { projectName: '芳烃塔能效优化', winner: '方案 A', saving: '3.72 万' },
  { projectName: '公用工程冷媒切换', winner: '方案 D', saving: '2.94 万' },
]

const aiAdviceList: AdviceItem[] = [
  {
    id: 1,
    project: '乙烯裂解换热站改造',
    time: '09:12',
    message: '经 A/B 对标，建议采用方案 B，主要优势集中在 OPEX 维度，15 年折现回收期缩短 1.2 年。',
  },
  {
    id: 2,
    project: '聚合反应釜保温重构',
    time: '08:46',
    message: '方案 B 的 M&R 下降 12.8%，但需关注 CAPEX 上浮与 Year 0 现金流挤占。',
  },
  {
    id: 3,
    project: '合成氨蒸汽回收升级',
    time: '08:15',
    message: '建议在峰电价时段切换低载工艺路线，可继续释放 0.9 万元的度电侧优化空间。',
  },
  {
    id: 4,
    project: '公用工程冷媒切换',
    time: '07:58',
    message: '当前风险成本波动高于行业中位，需补齐备件策略与维护资源挂载。',
  },
]

const cashflowYears = Array.from({ length: 16 }, (_, index) => `Year ${index}`)

const cashflowSeries = {
  capex: [42, 8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  opex: [0, 4.6, 4.3, 4.2, 4.1, 4.0, 3.8, 3.6, 3.5, 3.4, 3.2, 3.0, 2.8, 2.6, 2.5, 2.3],
  risk: [0, 1.6, 1.8, 1.4, 1.7, 1.5, 1.3, 1.5, 1.4, 1.2, 1.1, 1.0, 0.9, 0.9, 0.8, 0.7],
  mr: [0, 2.2, 2.1, 2.4, 2.0, 2.3, 2.6, 2.1, 2.2, 2.0, 1.8, 1.9, 1.7, 1.6, 1.4, 1.3],
}

const kpiCards = computed<KpiCard[]>(() => [
  {
    label: '累计发掘降本总额',
    subLabel: '核心北极星指标',
    value: '￥ 8,462.50 万',
    footer: '较上月新增 12 个优化快照闭环',
    tone: 'core',
  },
  {
    label: '纳管工程快照总数',
    subLabel: '工程建模基底',
    value: '1,286',
    footer: '覆盖 38 个重点工程项目',
    tone: 'blue',
  },
  {
    label: '累计完成 LCC 仿真次数',
    subLabel: '算力中枢吞吐',
    value: '9,482',
    footer: '近 7 日平均成功率 97.4%',
    tone: 'green',
  },
  {
    label: '全局平均综合度电价格',
    subLabel: '峰平谷折现口径',
    value: '0.684 元/kWh',
    footer: '峰段波动告警 3 条',
    tone: 'orange',
  },
])

const assetChartRef = ref<HTMLDivElement | null>(null)
const structureChartRef = ref<HTMLDivElement | null>(null)
const compareChartRef = ref<HTMLDivElement | null>(null)
const cashflowChartRef = ref<HTMLDivElement | null>(null)

let assetChart: echarts.ECharts | null = null
let structureChart: echarts.ECharts | null = null
let compareChart: echarts.ECharts | null = null
let cashflowChart: echarts.ECharts | null = null

function formatCount(value: number): string {
  return new Intl.NumberFormat('zh-CN').format(value)
}

function ensureChart(target: HTMLDivElement | null, current: echarts.ECharts | null): echarts.ECharts | null {
  if (!target) {
    return null
  }
  if (current && !current.isDisposed()) {
    return current
  }
  return echarts.init(target)
}

function buildAssetOption(): echarts.EChartsOption {
  return {
    backgroundColor: 'transparent',
    color: ['#38bdf8', '#10b981', '#f59e0b', '#818cf8'],
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(15, 23, 42, 0.94)',
      borderColor: '#334155',
      textStyle: { color: '#e2e8f0' },
    },
    title: {
      text: '主数据资源覆盖率',
      subtext: '条目数 / 占比双重表达',
      left: 'center',
      top: 6,
      textStyle: { color: '#f8fafc', fontSize: 16, fontWeight: 700 },
      subtextStyle: { color: '#94a3b8', fontSize: 11 },
    },
    series: [
      {
        type: 'pie',
        radius: ['18%', '72%'],
        center: ['50%', '58%'],
        roseType: 'area',
        itemStyle: {
          borderRadius: 8,
          borderColor: 'rgba(15, 23, 42, 0.9)',
          borderWidth: 2,
        },
        label: {
          color: '#cbd5e1',
          formatter: '{b}\n{c}',
        },
        data: assetInventory.map((item) => ({ name: item.name, value: item.value })),
      },
    ],
  }
}

function buildStructureOption(): echarts.EChartsOption {
  const total = costStructure.reduce((sum, item) => sum + item.value, 0)
  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(15, 23, 42, 0.94)',
      borderColor: '#334155',
      textStyle: { color: '#e2e8f0' },
      formatter: '{b}<br/>{c} 万元 ({d}%)',
    },
    title: {
      text: '定稿方案成本占比',
      subtext: '净现值总计锚定长期成本重心',
      left: 'center',
      top: 4,
      textStyle: { color: '#f8fafc', fontSize: 16, fontWeight: 700 },
      subtextStyle: { color: '#94a3b8', fontSize: 11 },
    },
    graphic: [
      {
        type: 'text',
        left: 'center',
        top: '43%',
        style: {
          text: '净现值总计',
          fill: '#94a3b8',
          fontSize: 12,
          fontWeight: 500,
        },
      },
      {
        type: 'text',
        left: 'center',
        top: '51%',
        style: {
          text: `${total.toLocaleString()} 万`,
          fill: '#f8fafc',
          fontSize: 26,
          fontWeight: 700,
        },
      },
    ],
    legend: {
      bottom: 4,
      textStyle: { color: '#cbd5e1' },
      itemWidth: 10,
      itemHeight: 10,
    },
    series: [
      {
        type: 'pie',
        radius: ['56%', '74%'],
        center: ['50%', '52%'],
        avoidLabelOverlap: true,
        label: { show: false },
        itemStyle: {
          borderColor: 'rgba(15, 23, 42, 0.92)',
          borderWidth: 3,
        },
        data: costStructure.map((item) => ({
          value: item.value,
          name: item.name,
          itemStyle: { color: item.color },
        })),
      },
    ],
  }
}

function buildCompareOption(): echarts.EChartsOption {
  const categories = Object.keys(focusProject.dimensions.A) as CostDimensionKey[]
  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: 'rgba(15, 23, 42, 0.94)',
      borderColor: '#334155',
      textStyle: { color: '#e2e8f0' },
      valueFormatter: (value) => `${value} 万元`,
    },
    legend: {
      top: 8,
      right: 12,
      textStyle: { color: '#cbd5e1' },
    },
    title: {
      text: '方案结构成本对标',
      subtext: '横向比较五维成本段的高低差',
      left: 14,
      top: 10,
      textStyle: { color: '#f8fafc', fontSize: 17, fontWeight: 700 },
      subtextStyle: { color: '#94a3b8', fontSize: 11 },
    },
    grid: {
      left: 42,
      right: 18,
      top: 72,
      bottom: 34,
    },
    xAxis: {
      type: 'category',
      data: categories,
      axisLine: { lineStyle: { color: '#475569' } },
      axisLabel: { color: '#cbd5e1' },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      name: '万元',
      nameTextStyle: { color: '#94a3b8' },
      splitLine: { lineStyle: { color: 'rgba(71, 85, 105, 0.25)' } },
      axisLabel: { color: '#94a3b8' },
    },
    series: [
      {
        name: '方案 A',
        type: 'bar',
        barWidth: 20,
        itemStyle: {
          borderRadius: [8, 8, 0, 0],
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#60a5fa' },
            { offset: 1, color: '#2563eb' },
          ]),
        },
        data: categories.map((key) => focusProject.dimensions.A[key]),
      },
      {
        name: '方案 B',
        type: 'bar',
        barWidth: 20,
        itemStyle: {
          borderRadius: [8, 8, 0, 0],
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#34d399' },
            { offset: 1, color: '#059669' },
          ]),
        },
        data: categories.map((key) => focusProject.dimensions.B[key]),
      },
    ],
  }
}

function buildCashflowOption(): echarts.EChartsOption {
  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: 'rgba(15, 23, 42, 0.94)',
      borderColor: '#334155',
      textStyle: { color: '#e2e8f0' },
      valueFormatter: (value) => `${value} 万元`,
    },
    title: {
      text: '15 年折现现金流压力带',
      subtext: '首年 CAPEX 起投，后续 OPEX / M&R / RISK 分层堆叠',
      left: 12,
      top: 8,
      textStyle: { color: '#f8fafc', fontSize: 15, fontWeight: 700 },
      subtextStyle: { color: '#94a3b8', fontSize: 11 },
    },
    legend: {
      top: 12,
      right: 10,
      textStyle: { color: '#cbd5e1' },
      itemWidth: 10,
      itemHeight: 10,
    },
    grid: {
      left: 44,
      right: 14,
      top: 72,
      bottom: 26,
    },
    xAxis: {
      type: 'category',
      data: cashflowYears,
      axisLabel: { color: '#94a3b8', interval: 1, fontSize: 10 },
      axisLine: { lineStyle: { color: '#475569' } },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#94a3b8' },
      splitLine: { lineStyle: { color: 'rgba(71, 85, 105, 0.22)' } },
    },
    series: [
      {
        name: 'CAPEX',
        type: 'bar',
        stack: 'total',
        data: cashflowSeries.capex,
        itemStyle: { color: '#38bdf8' },
      },
      {
        name: 'OPEX',
        type: 'bar',
        stack: 'total',
        data: cashflowSeries.opex,
        itemStyle: { color: '#10b981' },
      },
      {
        name: 'M&R',
        type: 'bar',
        stack: 'total',
        data: cashflowSeries.mr,
        itemStyle: { color: '#f59e0b' },
      },
      {
        name: 'RISK',
        type: 'bar',
        stack: 'total',
        data: cashflowSeries.risk,
        itemStyle: { color: '#fb7185' },
      },
    ],
  }
}

function renderCharts() {
  assetChart = ensureChart(assetChartRef.value, assetChart)
  structureChart = ensureChart(structureChartRef.value, structureChart)
  compareChart = ensureChart(compareChartRef.value, compareChart)
  cashflowChart = ensureChart(cashflowChartRef.value, cashflowChart)

  assetChart?.setOption(buildAssetOption())
  structureChart?.setOption(buildStructureOption())
  compareChart?.setOption(buildCompareOption())
  cashflowChart?.setOption(buildCashflowOption())
}

function resizeCharts() {
  assetChart?.resize()
  structureChart?.resize()
  compareChart?.resize()
  cashflowChart?.resize()
}

function disposeCharts() {
  assetChart?.dispose()
  structureChart?.dispose()
  compareChart?.dispose()
  cashflowChart?.dispose()
  assetChart = null
  structureChart = null
  compareChart = null
  cashflowChart = null
}

const headerCellStyle = (): CSSProperties => ({
  background: 'rgba(15, 23, 42, 0.95)',
  color: '#94a3b8',
  borderBottom: '1px solid rgba(71, 85, 105, 0.45)',
  fontWeight: '600',
})

const cellStyle = (): CSSProperties => ({
  background: 'rgba(15, 23, 42, 0)',
  color: '#e2e8f0',
  borderBottom: '1px solid rgba(71, 85, 105, 0.22)',
})

onMounted(async () => {
  await nextTick()
  renderCharts()
  window.addEventListener('resize', resizeCharts)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeCharts)
  disposeCharts()
})
</script>

<style scoped>
.dashboard-screen {
  --bg-start: #0f172a;
  --bg-end: #1e293b;
  --panel-bg: rgba(15, 23, 42, 0.72);
  --panel-strong: rgba(30, 41, 59, 0.82);
  --panel-border: rgba(51, 65, 85, 0.9);
  --text-primary: #f8fafc;
  --text-secondary: #94a3b8;
  --blue: #38bdf8;
  --green: #10b981;
  --orange: #f59e0b;
  --pink: #fb7185;
  position: relative;
  min-height: calc(100vh - 88px);
  padding: 24px;
  overflow: hidden;
  color: var(--text-primary);
  background:
    radial-gradient(circle at top left, rgba(56, 189, 248, 0.16), transparent 26%),
    radial-gradient(circle at 85% 12%, rgba(16, 185, 129, 0.14), transparent 22%),
    linear-gradient(135deg, var(--bg-start), var(--bg-end));
}

.screen-backdrop {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(148, 163, 184, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(148, 163, 184, 0.05) 1px, transparent 1px);
  background-size: 32px 32px;
  mask-image: linear-gradient(to bottom, rgba(0, 0, 0, 0.65), transparent 85%);
  pointer-events: none;
}

.top-bar,
.kpi-grid,
.main-grid {
  position: relative;
  z-index: 1;
}

.top-bar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 20px;
}

.title-block h1 {
  margin: 8px 0 10px;
  font-size: 34px;
  line-height: 1.1;
  letter-spacing: 0.02em;
}

.title-block p {
  margin: 0;
  max-width: 720px;
  color: var(--text-secondary);
  font-size: 14px;
}

.eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #7dd3fc;
  font-size: 12px;
  letter-spacing: 0.22em;
  text-transform: uppercase;
}

.time-chip {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 180px;
  padding: 14px 18px;
  border: 1px solid rgba(56, 189, 248, 0.3);
  border-radius: 18px;
  background: rgba(15, 23, 42, 0.75);
  box-shadow: 0 0 0 1px rgba(56, 189, 248, 0.05), 0 18px 40px rgba(2, 6, 23, 0.32);
}

.time-chip__label {
  color: var(--text-secondary);
  font-size: 12px;
}

.time-chip strong {
  font-size: 18px;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 18px;
}

.kpi-card {
  position: relative;
  padding: 18px 20px;
  border-radius: 20px;
  border: 1px solid rgba(71, 85, 105, 0.45);
  background: linear-gradient(180deg, rgba(30, 41, 59, 0.86), rgba(15, 23, 42, 0.92));
  overflow: hidden;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04), 0 16px 34px rgba(2, 6, 23, 0.32);
}

.kpi-card__glow {
  position: absolute;
  inset: auto auto -32px -24px;
  width: 150px;
  height: 150px;
  border-radius: 999px;
  filter: blur(10px);
  opacity: 0.28;
}

.kpi-card.core .kpi-card__glow {
  background: rgba(56, 189, 248, 0.9);
}

.kpi-card.blue .kpi-card__glow {
  background: rgba(96, 165, 250, 0.8);
}

.kpi-card.green .kpi-card__glow {
  background: rgba(16, 185, 129, 0.85);
}

.kpi-card.orange .kpi-card__glow {
  background: rgba(245, 158, 11, 0.85);
}

.kpi-card__header,
.kpi-card__footer {
  position: relative;
  z-index: 1;
}

.kpi-card__header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  color: var(--text-secondary);
  font-size: 12px;
}

.kpi-card__header span {
  color: var(--text-primary);
  font-size: 14px;
}

.kpi-card__value {
  position: relative;
  z-index: 1;
  margin: 18px 0 14px;
  font-size: 34px;
  font-weight: 700;
  line-height: 1.08;
  letter-spacing: 0.01em;
}

.kpi-card.core .kpi-card__value {
  color: #e0f2fe;
  text-shadow: 0 0 24px rgba(56, 189, 248, 0.35);
}

.kpi-card__footer {
  color: var(--text-secondary);
  font-size: 12px;
}

.main-grid {
  display: grid;
  grid-template-columns: 2fr 3fr 2fr;
  gap: 16px;
}

.left-column,
.center-column,
.right-column {
  display: grid;
  gap: 16px;
  min-width: 0;
}

.left-column {
  grid-template-rows: minmax(0, 1fr) minmax(0, 1fr);
}

.center-column {
  grid-template-rows: minmax(0, 1fr);
}

.right-column {
  grid-template-rows: 260px minmax(0, 1fr) 260px;
}

.panel-card {
  display: flex;
  flex-direction: column;
  min-height: 0;
  padding: 18px;
  border-radius: 22px;
  border: 1px solid rgba(51, 65, 85, 0.9);
  background: linear-gradient(180deg, rgba(30, 41, 59, 0.8), rgba(15, 23, 42, 0.86));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04), 0 18px 36px rgba(2, 6, 23, 0.34);
  backdrop-filter: blur(14px);
}

.panel-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.panel-head--battle {
  margin-bottom: 18px;
}

.panel-title {
  display: block;
  margin-bottom: 6px;
  font-size: 18px;
  font-weight: 700;
}

.panel-subtitle {
  margin: 0;
  color: var(--text-secondary);
  font-size: 12px;
  line-height: 1.5;
}

.panel-tag,
.panel-note {
  flex-shrink: 0;
  align-self: flex-start;
  padding: 5px 10px;
  border-radius: 999px;
  border: 1px solid rgba(71, 85, 105, 0.5);
  color: #cbd5e1;
  font-size: 11px;
  background: rgba(15, 23, 42, 0.6);
}

.panel-note-group {
  display: flex;
  gap: 8px;
}

.panel-note--accent {
  color: #7dd3fc;
}

.chart-block {
  min-height: 220px;
}

.chart-block--medium {
  height: 280px;
}

.chart-block--large {
  height: 340px;
}

.chart-block--hero {
  height: 420px;
}

.mini-stat-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-top: 14px;
}

.mini-stat-card {
  padding: 12px 14px;
  border-radius: 16px;
  border: 1px solid rgba(51, 65, 85, 0.72);
  background: rgba(15, 23, 42, 0.56);
}

.mini-stat-card__label,
.mini-stat-card small {
  display: block;
  color: var(--text-secondary);
}

.mini-stat-card strong {
  display: block;
  margin: 6px 0;
  font-size: 24px;
}

.battle-card {
  position: relative;
  overflow: hidden;
}

.battle-card::after {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at center, rgba(56, 189, 248, 0.12), transparent 54%);
  pointer-events: none;
}

.battle-highlight {
  position: relative;
  z-index: 1;
  display: grid;
  justify-items: center;
  gap: 8px;
  margin-bottom: 12px;
  padding: 18px 18px 16px;
  border-radius: 20px;
  border: 1px solid rgba(56, 189, 248, 0.22);
  background: linear-gradient(90deg, rgba(8, 47, 73, 0.72), rgba(6, 78, 59, 0.5));
}

.battle-highlight__label {
  color: #bae6fd;
  font-size: 13px;
  letter-spacing: 0.08em;
}

.battle-highlight__value {
  font-size: 48px;
  font-weight: 800;
  line-height: 1;
  color: #f8fafc;
  text-shadow: 0 0 24px rgba(56, 189, 248, 0.28);
}

.battle-highlight__footer {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 8px;
  color: var(--text-secondary);
  font-size: 13px;
}

.battle-highlight__footer strong {
  color: #34d399;
}

.scheme-summary-grid {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-top: 12px;
}

.scheme-summary-card {
  padding: 14px 16px;
  border-radius: 16px;
  border: 1px solid rgba(51, 65, 85, 0.72);
  background: rgba(15, 23, 42, 0.55);
}

.scheme-summary-card__header {
  display: flex;
  justify-content: space-between;
  color: var(--text-secondary);
  font-size: 12px;
}

.scheme-summary-card strong {
  display: block;
  margin: 8px 0;
  font-size: 26px;
}

.scheme-summary-card p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 12px;
  line-height: 1.5;
}

.ranking-card :deep(.el-table) {
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-border-color: rgba(71, 85, 105, 0.32);
  --el-table-header-bg-color: rgba(15, 23, 42, 0.95);
  --el-table-row-hover-bg-color: rgba(30, 41, 59, 0.66);
  --el-fill-color-lighter: transparent;
  border-radius: 16px;
  overflow: hidden;
}

.ranking-card :deep(.el-table__inner-wrapper::before) {
  display: none;
}

.ranking-card :deep(.el-table th.el-table__cell),
.ranking-card :deep(.el-table td.el-table__cell) {
  background: transparent;
}

.ai-wall-list {
  display: grid;
  gap: 12px;
  overflow: auto;
  padding-right: 4px;
}

.ai-wall-item {
  display: grid;
  grid-template-columns: 14px minmax(0, 1fr);
  gap: 12px;
  padding: 12px 14px;
  border-radius: 16px;
  border: 1px solid rgba(51, 65, 85, 0.72);
  background: rgba(15, 23, 42, 0.58);
}

.ai-wall-item__dot {
  width: 10px;
  height: 10px;
  margin-top: 6px;
  border-radius: 999px;
  background: linear-gradient(180deg, #38bdf8, #10b981);
  box-shadow: 0 0 14px rgba(56, 189, 248, 0.4);
}

.ai-wall-item__meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 6px;
  color: #cbd5e1;
  font-size: 12px;
}

.ai-wall-item__meta small {
  color: var(--text-secondary);
}

.ai-wall-item p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1.6;
}

@media (max-width: 1440px) {
  .kpi-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .main-grid {
    grid-template-columns: 1fr;
  }

  .left-column,
  .center-column,
  .right-column {
    grid-template-rows: auto;
  }

  .right-column {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 960px) {
  .dashboard-screen {
    padding: 16px;
  }

  .top-bar {
    flex-direction: column;
  }

  .title-block h1 {
    font-size: 28px;
  }

  .kpi-grid,
  .mini-stat-grid,
  .scheme-summary-grid,
  .right-column {
    grid-template-columns: 1fr;
  }

  .battle-highlight__value {
    font-size: 38px;
  }

  .chart-block--hero {
    height: 340px;
  }
}
</style>

