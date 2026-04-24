<template>
  <div class="cost-ledger-view">
    <div class="page-header">
      <div class="header-left">
        <el-button link @click="handleBack">
          <el-icon><ArrowLeft /></el-icon>
          返回
        </el-button>
        <div class="header-title">
          <h2>静态成本台账</h2>
          <div class="snapshot-info" v-if="snapshotInfo">
            <el-tag type="info" size="small">{{ snapshotInfo.code }}</el-tag>
            <span class="snapshot-name">{{ snapshotInfo.name }}</span>
          </div>
        </div>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="handleExport">
          <el-icon><Download /></el-icon>
          导出报表
        </el-button>
      </div>
    </div>

    <div class="page-content" v-loading="loading">
      <div class="metrics-cards">
        <div class="metric-card primary">
          <div class="metric-icon">
            <el-icon :size="32"><Coin /></el-icon>
          </div>
          <div class="metric-content">
            <div class="metric-label">单件理论总成本</div>
            <div class="metric-value">{{ formatCurrency(costData.total_cost) }}</div>
            <div class="metric-unit">元/件</div>
          </div>
        </div>
        
        <div class="metric-card">
          <div class="metric-icon machine">
            <el-icon :size="28"><SetUp /></el-icon>
          </div>
          <div class="metric-content">
            <div class="metric-label">机器折旧费</div>
            <div class="metric-value">{{ formatCurrency(costData.cost_breakdown.total_machine) }}</div>
            <div class="metric-percent">{{ getPercent(costData.cost_breakdown.total_machine) }}%</div>
          </div>
        </div>
        
        <div class="metric-card">
          <div class="metric-icon labor">
            <el-icon :size="28"><User /></el-icon>
          </div>
          <div class="metric-content">
            <div class="metric-label">人工费</div>
            <div class="metric-value">{{ formatCurrency(costData.cost_breakdown.total_labor) }}</div>
            <div class="metric-percent">{{ getPercent(costData.cost_breakdown.total_labor) }}%</div>
          </div>
        </div>
        
        <div class="metric-card">
          <div class="metric-icon material">
            <el-icon :size="28"><Box /></el-icon>
          </div>
          <div class="metric-content">
            <div class="metric-label">辅材费</div>
            <div class="metric-value">{{ formatCurrency(costData.cost_breakdown.total_material) }}</div>
            <div class="metric-percent">{{ getPercent(costData.cost_breakdown.total_material) }}%</div>
          </div>
        </div>
        
        <div class="metric-card">
          <div class="metric-icon outsource">
            <el-icon :size="28"><Link /></el-icon>
          </div>
          <div class="metric-content">
            <div class="metric-label">委外加工费</div>
            <div class="metric-value">{{ formatCurrency(costData.cost_breakdown.total_outsource) }}</div>
            <div class="metric-percent">{{ getPercent(costData.cost_breakdown.total_outsource) }}%</div>
          </div>
        </div>
      </div>

      <div class="main-content">
        <div class="chart-panel">
          <div class="panel-header">
            <span>成本结构分布</span>
          </div>
          <div class="panel-body">
            <div ref="pieChartRef" class="pie-chart"></div>
          </div>
        </div>

        <div class="table-panel">
          <div class="panel-header">
            <span>BOM 成本明细</span>
            <el-button-group size="small">
              <el-button :type="expandAll ? 'primary' : 'default'" @click="toggleExpandAll">
                {{ expandAll ? '收起全部' : '展开全部' }}
              </el-button>
            </el-button-group>
          </div>
          <div class="panel-body">
            <el-table
              ref="tableRef"
              :data="tableData"
              row-key="id"
              :default-expand-all="expandAll"
              :tree-props="{ children: 'children', hasChildren: 'hasChildren' }"
              border
              stripe
              size="small"
            >
              <el-table-column prop="node_name" label="节点名称" min-width="180" fixed>
                <template #default="{ row }">
                  <div class="node-name-cell">
                    <el-icon v-if="row.node_type === 'ASSEMBLY'" class="type-icon assembly">
                      <FolderOpened />
                    </el-icon>
                    <el-icon v-else class="type-icon part">
                      <Document />
                    </el-icon>
                    <span>{{ row.node_name }}</span>
                  </div>
                </template>
              </el-table-column>
              <el-table-column prop="code" label="节点编码" width="120" />
              <el-table-column prop="quantity" label="数量" width="80" align="right">
                <template #default="{ row }">
                  {{ row.quantity || '-' }}
                </template>
              </el-table-column>
              <el-table-column label="自身工序成本" width="120" align="right">
                <template #default="{ row }">
                  <span class="cost-own">
                    {{ formatCurrency(row.cost_detail?.own_cost?.total_cost || 0) }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column label="累计总成本" width="130" align="right">
                <template #default="{ row }">
                  <span class="cost-total">
                    {{ formatCurrency(row.cost_detail?.total_cost || 0) }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column label="成本结构" min-width="200">
                <template #default="{ row }">
                  <div class="cost-breakdown" v-if="row.cost_detail">
                    <el-tag v-if="row.cost_detail.machine_cost > 0" size="small" type="info" class="breakdown-tag">
                      机: {{ formatCurrency(row.cost_detail.machine_cost) }}
                    </el-tag>
                    <el-tag v-if="row.cost_detail.labor_cost > 0" size="small" type="success" class="breakdown-tag">
                      工: {{ formatCurrency(row.cost_detail.labor_cost) }}
                    </el-tag>
                    <el-tag v-if="row.cost_detail.material_cost > 0" size="small" type="warning" class="breakdown-tag">
                      料: {{ formatCurrency(row.cost_detail.material_cost) }}
                    </el-tag>
                    <el-tag v-if="row.cost_detail.outsource_cost > 0" size="small" type="danger" class="breakdown-tag">
                      外: {{ formatCurrency(row.cost_detail.outsource_cost) }}
                    </el-tag>
                    <span v-if="!hasAnyCost(row.cost_detail)" class="no-cost">-</span>
                  </div>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, computed, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import {
  ArrowLeft,
  Download,
  Coin,
  SetUp,
  User,
  Box,
  Link,
  FolderOpened,
  Document,
} from '@element-plus/icons-vue'
import { getStaticCostLedger, type CostDetail, type BomNode, type CostBreakdown } from '@/api/costing'

interface CostData {
  total_cost: number
  cost_breakdown: CostBreakdown
  annotated_bom_tree: BomNode[]
  route_costs: any[]
}

const router = useRouter()
const route = useRoute()
const loading = ref(false)
const expandAll = ref(true)
const pieChartRef = ref<HTMLElement>()
let pieChart: echarts.ECharts | null = null

const snapshotInfo = ref<{
  code: string
  name: string
} | null>(null)

const costData = reactive<CostData>({
  total_cost: 0,
  cost_breakdown: {
    total_machine: 0,
    total_labor: 0,
    total_material: 0,
    total_outsource: 0,
    total_cost: 0,
  },
  annotated_bom_tree: [],
  route_costs: [],
})

const tableData = computed(() => costData.annotated_bom_tree)

const formatCurrency = (value: number | undefined | null): string => {
  if (value === undefined || value === null) return '0.00'
  return value.toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

const getPercent = (value: number | undefined | null): string => {
  if (!costData.total_cost || costData.total_cost === 0) return '0.0'
  if (value === undefined || value === null) return '0.0'
  return ((value / costData.total_cost) * 100).toFixed(1)
}

const hasAnyCost = (detail: CostDetail | undefined): boolean => {
  if (!detail) return false
  return (
    detail.machine_cost > 0 ||
    detail.labor_cost > 0 ||
    detail.material_cost > 0 ||
    detail.outsource_cost > 0
  )
}

const handleBack = () => {
  router.back()
}

const handleExport = () => {
  console.log('Export cost report')
}

const toggleExpandAll = () => {
  expandAll.value = !expandAll.value
}

const initPieChart = () => {
  if (!pieChartRef.value) return

  pieChart = echarts.init(pieChartRef.value)

  const chartData = [
    { value: costData.cost_breakdown.total_machine, name: '机器折旧费' },
    { value: costData.cost_breakdown.total_labor, name: '人工费' },
    { value: costData.cost_breakdown.total_material, name: '辅材费' },
    { value: costData.cost_breakdown.total_outsource, name: '委外加工费' },
  ].filter(item => item.value > 0)

  const option: echarts.EChartsOption = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} 元 ({d}%)',
    },
    legend: {
      orient: 'horizontal',
      bottom: '5%',
      textStyle: {
        color: '#a0aec0',
        fontSize: 12,
      },
    },
    series: [
      {
        name: '成本结构',
        type: 'pie',
        radius: ['45%', '70%'],
        center: ['50%', '45%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 8,
          borderColor: '#1a2332',
          borderWidth: 2,
        },
        label: {
          show: true,
          position: 'outside',
          formatter: '{b}\n{d}%',
          color: '#a0aec0',
          fontSize: 11,
        },
        labelLine: {
          show: true,
          lineStyle: {
            color: '#4a5568',
          },
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 14,
            fontWeight: 'bold',
          },
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)',
          },
        },
        data: chartData,
        color: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444'],
      },
    ],
  }

  pieChart.setOption(option)
}

const loadCostData = async () => {
  const snapshotId = route.params.snapshotId
  
  if (!snapshotId) {
    ElMessage.warning('缺少快照 ID 参数')
    return
  }
  
  loading.value = true

  try {
    const res = await getStaticCostLedger(Number(snapshotId))
    const data = res.data
    
    Object.assign(costData, {
      total_cost: data.total_cost,
      cost_breakdown: data.cost_breakdown,
      annotated_bom_tree: data.annotated_bom_tree,
      route_costs: data.route_costs,
    })
    
    snapshotInfo.value = {
      code: `快照 #${snapshotId}`,
      name: '静态成本台账',
    }

    await nextTick()
    initPieChart()
  } catch (error: any) {
    console.error('加载成本数据失败:', error)
    ElMessage.error(error.response?.data?.message || '加载成本数据失败')
  } finally {
    loading.value = false
  }
}

const handleResize = () => {
  pieChart?.resize()
}

onMounted(() => {
  loadCostData()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  pieChart?.dispose()
})
</script>

<style scoped>
.cost-ledger-view {
  min-height: 100vh;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: rgba(30, 41, 59, 0.8);
  border-bottom: 1px solid rgba(71, 85, 105, 0.5);
  backdrop-filter: blur(10px);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-left .el-button {
  color: #94a3b8;
  font-size: 14px;
}

.header-left .el-button:hover {
  color: #3b82f6;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-title h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #f1f5f9;
}

.snapshot-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.snapshot-name {
  color: #94a3b8;
  font-size: 14px;
}

.page-content {
  padding: 20px 24px;
}

.metrics-cards {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.metric-card {
  background: rgba(30, 41, 59, 0.6);
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  border: 1px solid rgba(71, 85, 105, 0.3);
  transition: all 0.3s ease;
}

.metric-card:hover {
  border-color: rgba(59, 130, 246, 0.5);
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
}

.metric-card.primary {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.2) 0%, rgba(37, 99, 235, 0.3) 100%);
  border-color: rgba(59, 130, 246, 0.5);
  grid-column: span 1;
}

.metric-card.primary .metric-icon {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4);
}

.metric-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.metric-icon.machine {
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
}

.metric-icon.labor {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
}

.metric-icon.material {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
}

.metric-icon.outsource {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
}

.metric-content {
  flex: 1;
  min-width: 0;
}

.metric-label {
  font-size: 13px;
  color: #94a3b8;
  margin-bottom: 4px;
}

.metric-value {
  font-size: 22px;
  font-weight: 700;
  color: #f1f5f9;
  line-height: 1.2;
}

.metric-card.primary .metric-value {
  font-size: 28px;
}

.metric-unit {
  font-size: 12px;
  color: #64748b;
  margin-top: 2px;
}

.metric-percent {
  font-size: 12px;
  color: #64748b;
  margin-top: 2px;
}

.main-content {
  display: grid;
  grid-template-columns: 30% 70%;
  gap: 20px;
  min-height: calc(100vh - 280px);
}

.chart-panel,
.table-panel {
  background: rgba(30, 41, 59, 0.6);
  border-radius: 12px;
  border: 1px solid rgba(71, 85, 105, 0.3);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(71, 85, 105, 0.3);
  color: #f1f5f9;
  font-weight: 500;
  font-size: 15px;
}

.panel-body {
  flex: 1;
  padding: 16px;
  overflow: auto;
}

.pie-chart {
  width: 100%;
  height: 100%;
  min-height: 300px;
}

.table-panel .panel-body {
  padding: 0;
}

.table-panel :deep(.el-table) {
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: rgba(51, 65, 85, 0.5);
  --el-table-row-hover-bg-color: rgba(59, 130, 246, 0.1);
  --el-table-border-color: rgba(71, 85, 105, 0.3);
  --el-table-text-color: #e2e8f0;
  --el-table-header-text-color: #94a3b8;
}

.table-panel :deep(.el-table th.el-table__cell) {
  background: rgba(51, 65, 85, 0.5);
  font-weight: 600;
}

.table-panel :deep(.el-table--striped .el-table__body tr.el-table__row--striped td.el-table__cell) {
  background: rgba(51, 65, 85, 0.2);
}

.node-name-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.type-icon {
  font-size: 16px;
}

.type-icon.assembly {
  color: #3b82f6;
}

.type-icon.part {
  color: #10b981;
}

.cost-own {
  color: #94a3b8;
}

.cost-total {
  font-weight: 600;
  color: #f1f5f9;
}

.cost-breakdown {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.breakdown-tag {
  font-size: 11px;
  padding: 2px 6px;
}

.no-cost {
  color: #64748b;
  font-size: 12px;
}

@media (max-width: 1400px) {
  .metrics-cards {
    grid-template-columns: repeat(3, 1fr);
  }
  
  .metric-card.primary {
    grid-column: span 1;
  }
}

@media (max-width: 1200px) {
  .main-content {
    grid-template-columns: 1fr;
  }
  
  .chart-panel {
    min-height: 350px;
  }
}

@media (max-width: 900px) {
  .metrics-cards {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
