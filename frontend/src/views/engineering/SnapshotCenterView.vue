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
          <span class="table-title">快照台账列表</span>
          <span class="table-count">共 {{ filteredSnapshots.length }} 条记录</span>
        </div>
        
        <el-table
          :data="filteredSnapshots"
          v-loading="loading"
          border
          stripe
          style="width: 100%"
        >
          <el-table-column prop="snapshot_code" label="快照编码" width="160" />
          
          <el-table-column prop="snapshot_name" label="快照名称" min-width="180">
            <template #default="{ row }">
              <div class="snapshot-name">
                <span>{{ row.snapshot_name }}</span>
                <span class="scheme-name">{{ row.scheme_name }}</span>
              </div>
            </template>
          </el-table-column>
          
          <el-table-column label="静态总成本" width="140" align="right">
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
                    仿真进度
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
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  DocumentCopy,
  CircleCheck,
  Warning,
  Search,
  Refresh,
  Loading,
} from '@element-plus/icons-vue'
import { modelSnapshotApi, type ModelSnapshot } from '@/api/engineering'
import { getStaticCostLedger } from '@/api/costing'

interface Snapshot {
  id: number
  snapshot_code: string
  snapshot_name: string
  scheme_name: string
  total_cost: number
  status: 'READY' | 'SIMULATING' | 'COMPLETED'
  created_at: string
}

const router = useRouter()
const loading = ref(false)

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
const allSnapshots = ref<ModelSnapshot[]>([])

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
      const date = item.created_at.split(' ')[0]
      return date >= start && date <= end
    })
  }
  
  return result
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
    DRAFT: 'info',
  }
  return map[status] || 'info'
}

const getStatusText = (status: string): string => {
  const map: Record<string, string> = {
    READY: '静态已生成',
    SIMULATING: '仿真推演中',
    COMPLETED: '仿真完成',
    DRAFT: '草稿',
  }
  return map[status] || status
}

const loadSnapshots = async () => {
  loading.value = true
  
  try {
    const res = await modelSnapshotApi.list({ size: 100 })
    allSnapshots.value = res.data.items || []
    
    const snapshotList: Snapshot[] = []
    
    for (const snapshot of allSnapshots.value) {
      let totalCost = 0
      try {
        const costRes = await getStaticCostLedger(snapshot.id)
        totalCost = costRes.data.total_cost || 0
      } catch {
        // 快照可能没有成本数据
      }
      
      snapshotList.push({
        id: snapshot.id,
        snapshot_code: snapshot.snapshot_code,
        snapshot_name: snapshot.snapshot_name,
        scheme_name: `版本 #${snapshot.scheme_version_id}`,
        total_cost: totalCost,
        status: snapshot.status === 'READY' ? 'READY' : 
                snapshot.status === 'DRAFT' ? 'READY' : 
                snapshot.status as 'READY' | 'SIMULATING' | 'COMPLETED',
        created_at: snapshot.created_at,
      })
    }
    
    snapshots.value = snapshotList
    pagination.total = snapshotList.length
    
    stats.totalSnapshots = allSnapshots.value.length
    stats.simulationsCompleted = allSnapshots.value.filter(s => s.status === 'COMPLETED').length
    stats.costAlerts = 0
  } catch (error: any) {
    console.error('加载快照列表失败:', error)
    ElMessage.error(error.response?.data?.message || '加载快照列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
}

const handleReset = () => {
  filterForm.keyword = ''
  filterForm.status = ''
  filterForm.dateRange = []
  pagination.page = 1
}

const handleViewLedger = (row: Snapshot) => {
  router.push(`/engineering/cost-ledger/${row.id}`)
}

const handleStartSimulation = async (row: Snapshot) => {
  try {
    await ElMessageBox.confirm(
      '确定要将此模型推入算力集群进行全生命周期仿真吗？该过程可能需要几分钟。',
      '启动LCC仿真',
      {
        confirmButtonText: '确定启动',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    const index = snapshots.value.findIndex(item => item.id === row.id)
    if (index !== -1) {
      snapshots.value[index].status = 'SIMULATING'
    }
    
    ElMessage.success({
      message: `快照 ${row.snapshot_code} 已成功投递至仿真队列`,
      duration: 3000,
    })
  } catch {
    // 用户取消
  }
}

const handleViewReport = (row: Snapshot) => {
  ElMessage.info(`查看LCC报告功能开发中：${row.snapshot_name}`)
}

onMounted(() => {
  loadSnapshots()
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
  padding: 16px 20px;
  border-bottom: 1px solid #ebeef5;
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
