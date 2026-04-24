<template>
  <div class="snapshot-inventory-panel">
    <div class="stats-cards">
      <div class="stat-card">
        <div class="stat-icon total">
          <el-icon :size="24"><DocumentCopy /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.totalSnapshots }}</div>
          <div class="stat-label">当前范围快照数</div>
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
      <el-form :inline="true" class="filter-form">
        <el-form-item label="快照检索">
          <el-input
            v-model="filterForm.keyword"
            placeholder="请输入项目、产品、方案或快照名称"
            clearable
            style="width: 260px"
            @keyup.enter="handleSearch"
          />
        </el-form-item>

        <el-form-item label="状态">
          <el-select v-model="filterForm.status" placeholder="全部状态" clearable style="width: 140px">
            <el-option label="全部" value="" />
            <el-option label="静态已生成" value="READY" />
            <el-option label="仿真推演中" value="SIMULATING" />
            <el-option label="仿真完成" value="COMPLETED" />
            <el-option label="仿真失败" value="FAILED" />
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
          <span class="table-title">{{ modeTitle }}</span>
          <span class="table-count">{{ scopeLabel }} · 共 {{ filteredSnapshots.length }} 条</span>
        </div>
        <div class="table-header-actions">
          <el-button
            v-if="isDecisionMode"
            type="primary"
            :disabled="!canCompareSelectedSnapshots"
            @click="emit('compare', selectedSnapshots)"
          >
            📊 多方案 LCC 对标
          </el-button>
        </div>
      </div>

      <el-table
        ref="tableRef"
        :data="paginatedSnapshots"
        row-key="id"
        v-loading="loading"
        border
        stripe
        @selection-change="handleSelectionChange"
      >
        <template #empty>
          <el-empty :description="emptyDescription" :image-size="88" />
        </template>
        <el-table-column v-if="isDecisionMode" type="selection" width="52" fixed="left" />
        <el-table-column prop="snapshot_code" label="快照编码" width="160" />

        <el-table-column prop="snapshot_name" label="快照名称" min-width="220">
          <template #default="{ row }">
            <div class="snapshot-name">
              <span>{{ row.snapshot_name }}</span>
              <span class="scheme-name">{{ row.product_name }} / {{ row.scheme_name }} / {{ row.version_label }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="project_name" label="项目" width="160" show-overflow-tooltip />
        <el-table-column prop="product_name" label="产品" width="160" show-overflow-tooltip />

        <el-table-column label="总成本" width="140" align="right">
          <template #default="{ row }">
            <span class="cost-value">{{ formatCurrency(row.total_cost) }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="created_at" label="生成时间" width="170" />

        <el-table-column prop="status" label="当前状态" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" :class="{ simulating: row.status === 'SIMULATING' }">
              <el-icon v-if="row.status === 'SIMULATING'" class="is-loading" style="margin-right: 4px">
                <Loading />
              </el-icon>
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="300" fixed="right" align="center">
          <template #default="{ row }">
            <div class="action-buttons">
              <template v-if="row.status === 'READY'">
                <el-button link type="primary" @click="emit('view-ledger', row)">查看台账</el-button>
                <el-button type="primary" size="small" @click="emit('start-simulation', row)">启动LCC仿真</el-button>
              </template>

              <template v-else-if="row.status === 'SIMULATING'">
                <el-button link disabled>
                  <el-icon class="is-loading"><Loading /></el-icon>
                  推演中...
                </el-button>
              </template>

              <template v-else-if="row.status === 'COMPLETED'">
                <el-button link type="primary" @click="emit('view-ledger', row)">查看台账</el-button>
                <el-button type="success" size="small" @click="emit('view-report', row)">查看LCC报告</el-button>
              </template>

              <template v-else-if="row.status === 'FAILED'">
                <el-button link type="primary" @click="emit('view-ledger', row)">查看台账</el-button>
                <el-button type="danger" size="small" @click="emit('start-simulation', row)">重新仿真</el-button>
              </template>

              <template v-else>
                <el-button link disabled>暂不可用</el-button>
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
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { CircleCheck, DocumentCopy, Loading, Refresh, Search, Warning } from '@element-plus/icons-vue'
import type { ElTable } from 'element-plus'
import type { SnapshotInventoryRow, SnapshotPageMode, SnapshotStatus } from '@/types/engineeringSnapshots'

const props = defineProps<{
  loading: boolean
  rows: SnapshotInventoryRow[]
  mode: SnapshotPageMode
  scopeLabel: string
}>()

const emit = defineEmits<{
  (e: 'compare', rows: SnapshotInventoryRow[]): void
  (e: 'view-ledger', row: SnapshotInventoryRow): void
  (e: 'start-simulation', row: SnapshotInventoryRow): void
  (e: 'view-report', row: SnapshotInventoryRow): void
}>()

const tableRef = ref<InstanceType<typeof ElTable>>()
const selectedSnapshots = ref<SnapshotInventoryRow[]>([])
const filterForm = reactive({
  keyword: '',
  status: '' as '' | SnapshotStatus,
  dateRange: [] as string[],
})
const pagination = reactive({
  page: 1,
  size: 10,
})

const isDecisionMode = computed(() => props.mode === 'decision-center')
const modeTitle = computed(() => (isDecisionMode.value ? '决策候选快照列表' : '产品快照列表'))
const emptyDescription = computed(() => {
  if (props.scopeLabel === '全部项目快照') {
    return isDecisionMode.value ? '暂无可用于决策对标的已归档快照，请先在产品方案下生成快照。' : '暂无产品快照，请先从方案版本生成快照。'
  }
  return `当前范围“${props.scopeLabel}”下暂无快照记录`
})

const filteredSnapshots = computed(() => {
  let result = [...props.rows]

  if (filterForm.keyword) {
    const keyword = filterForm.keyword.toLowerCase()
    result = result.filter((item) =>
      [item.snapshot_name, item.snapshot_code, item.project_name, item.product_name, item.scheme_name]
        .some((field) => field.toLowerCase().includes(keyword)),
    )
  }

  if (filterForm.status) {
    result = result.filter((item) => item.status === filterForm.status)
  }

  if (filterForm.dateRange.length === 2) {
    const [start, end] = filterForm.dateRange
    result = result.filter((item) => {
      const date = item.created_at.slice(0, 10)
      return date >= start && date <= end
    })
  }

  return result
})

const paginatedSnapshots = computed(() => {
  const start = (pagination.page - 1) * pagination.size
  return filteredSnapshots.value.slice(start, start + pagination.size)
})

const stats = computed(() => ({
  totalSnapshots: filteredSnapshots.value.length,
  simulationsCompleted: filteredSnapshots.value.filter((item) => item.status === 'COMPLETED').length,
  costAlerts: filteredSnapshots.value.filter((item) => item.status === 'FAILED').length,
}))

const canCompareSelectedSnapshots = computed(() => {
  return selectedSnapshots.value.length === 2 && selectedSnapshots.value.every((item) => item.status === 'COMPLETED')
})

watch(filteredSnapshots, (rows) => {
  const visibleIds = new Set(rows.map((item) => item.id))
  selectedSnapshots.value = selectedSnapshots.value.filter((item) => visibleIds.has(item.id))
  if (pagination.page > 1 && (pagination.page - 1) * pagination.size >= rows.length) {
    pagination.page = 1
  }
})

watch(() => props.rows, () => {
  selectedSnapshots.value = []
  tableRef.value?.clearSelection()
})

function handleSearch() {
  pagination.page = 1
}

function handleReset() {
  filterForm.keyword = ''
  filterForm.status = ''
  filterForm.dateRange = []
  pagination.page = 1
  selectedSnapshots.value = []
  tableRef.value?.clearSelection()
}

function handleSelectionChange(rows: SnapshotInventoryRow[]) {
  selectedSnapshots.value = rows
}

function formatCurrency(value: number): string {
  return '￥' + value.toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

function getStatusType(status: SnapshotStatus): string {
  const map: Record<SnapshotStatus, string> = {
    READY: 'primary',
    SIMULATING: 'warning',
    COMPLETED: 'success',
    FAILED: 'danger',
    DRAFT: 'info',
    ARCHIVED: 'info',
  }
  return map[status] || 'info'
}

function getStatusText(status: SnapshotStatus): string {
  const map: Record<SnapshotStatus, string> = {
    READY: '静态已生成',
    SIMULATING: '仿真推演中',
    COMPLETED: '仿真完成',
    FAILED: '仿真失败',
    DRAFT: '草稿',
    ARCHIVED: '已归档',
  }
  return map[status] || status
}
</script>

<style scoped>
.snapshot-inventory-panel {
  display: flex;
  flex-direction: column;
  gap: 20px;
  min-height: 0;
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px 24px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
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

.table-section {
  min-height: 0;
  display: flex;
  flex-direction: column;
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

.scheme-name {
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

.pagination-section {
  display: flex;
  justify-content: flex-end;
  padding: 16px 20px;
  border-top: 1px solid #ebeef5;
}

.simulating {
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}
</style>