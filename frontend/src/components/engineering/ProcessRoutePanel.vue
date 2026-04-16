<template>
  <div class="process-route-panel">
    <!-- 面板标题 -->
    <div class="panel-header">
      <h3>工艺路线编排</h3>
      <el-button 
        type="primary" 
        size="small"
        :disabled="!canAddProcess"
        @click="handleAddProcess"
      >
        + 添加标准工序
      </el-button>
    </div>
    
    <!-- 内容区域 -->
    <div class="panel-body">
      <!-- 空状态：未选中节点 -->
      <el-empty 
        v-if="!hasSelectedBomNode"
        description="请先在左侧选择一个零件节点"
        :image-size="120"
      />
      
      <!-- 空状态：选中的是装配节点 -->
      <el-empty 
        v-else-if="selectedBomNode?.node_type === 'ASSEMBLY'"
        description="装配节点无法配置工艺路线，请选择叶子零件节点"
        :image-size="120"
      />
      
      <!-- 工序列表 -->
      <div v-else class="process-list">
        <el-table
          v-loading="routesLoading || stepsLoading"
          :data="routeSteps"
          highlight-current-row
          @current-change="handleCurrentChange"
          style="width: 100%"
        >
          <el-table-column type="index" label="序号" width="60" align="center" />
          
          <el-table-column prop="process.name" label="工序名称" min-width="150">
            <template #default="{ row }">
              <div class="process-name">
                <span>{{ row.process?.name || '-' }}</span>
                <el-tag v-if="row.process?.code" size="small" type="info">
                  {{ row.process.code }}
                </el-tag>
              </div>
            </template>
          </el-table-column>
          
          <el-table-column prop="process.setup_time" label="准备工时(h)" width="120" align="center">
            <template #default="{ row }">
              {{ row.process?.setup_time || '-' }}
            </template>
          </el-table-column>
          
          <el-table-column prop="process.standard_time" label="运行工时(h)" width="120" align="center">
            <template #default="{ row }">
              {{ row.process?.standard_time || '-' }}
            </template>
          </el-table-column>
          
          <el-table-column label="操作" width="140" align="center" fixed="right">
            <template #default="{ row, $index }">
              <el-button 
                link 
                type="primary" 
                size="small"
                :disabled="$index === 0"
                @click="handleMoveUp($index)"
              >
                上移
              </el-button>
              <el-button 
                link 
                type="primary" 
                size="small"
                :disabled="$index === routeSteps.length - 1"
                @click="handleMoveDown($index)"
              >
                下移
              </el-button>
              <el-button 
                link 
                type="danger" 
                size="small"
                @click="handleDelete(row)"
              >
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        
        <!-- 空状态：无工序 -->
        <el-empty 
          v-if="!routesLoading && !stepsLoading && routeSteps.length === 0"
          description="暂无工序，请点击上方按钮添加标准工序"
          :image-size="100"
        />
      </div>
    </div>
    
    <!-- 标准工艺选择器弹窗 -->
    <ProcessSelectorDialog 
      v-model="selectorVisible"
      @select="handleProcessSelect"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useEngineeringStore } from '@/stores/engineering'
import type { RouteStepBindWithProcess } from '@/api/engineering'
import ProcessSelectorDialog from './ProcessSelectorDialog.vue'

const store = useEngineeringStore()

// 从 Store 获取状态
const hasSelectedBomNode = computed(() => store.hasSelectedBomNode)
const selectedBomNode = computed(() => store.selectedBomNode)
const routeSteps = computed(() => store.routeSteps)
const routesLoading = computed(() => store.routesLoading)
const stepsLoading = computed(() => store.stepsLoading)

// 是否可以添加工序
const canAddProcess = computed(() => {
  return hasSelectedBomNode.value && selectedBomNode.value?.node_type === 'PART'
})

// 标准工艺选择器弹窗
const selectorVisible = ref(false)

// 当前行变化
function handleCurrentChange(currentRow: RouteStepBindWithProcess | null) {
  store.selectStep(currentRow)
}

// 添加标准工序
function handleAddProcess() {
  selectorVisible.value = true
}

// 选择标准工艺后的回调
async function handleProcessSelect(processId: number) {
  await store.addRouteStep(processId)
  selectorVisible.value = false
}

// 上移工序
async function handleMoveUp(index: number) {
  if (index === 0) return
  
  const newSteps = [...routeSteps.value]
  const temp = newSteps[index - 1]
  newSteps[index - 1] = newSteps[index]
  newSteps[index] = temp
  
  const stepIds = newSteps.map(step => step.id)
  await store.reorderRouteSteps(stepIds)
}

// 下移工序
async function handleMoveDown(index: number) {
  if (index === routeSteps.value.length - 1) return
  
  const newSteps = [...routeSteps.value]
  const temp = newSteps[index + 1]
  newSteps[index + 1] = newSteps[index]
  newSteps[index] = temp
  
  const stepIds = newSteps.map(step => step.id)
  await store.reorderRouteSteps(stepIds)
}

// 删除工序
async function handleDelete(row: RouteStepBindWithProcess) {
  try {
    await ElMessageBox.confirm(
      `确定要删除工序 [${row.process?.name || '未知'}] 吗？`,
      '危险操作',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning',
        center: true,
      }
    )
    
    await store.deleteRouteStep(row.id)
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') {
      console.error('Delete failed:', error)
    }
  }
}
</script>

<style scoped>
.process-route-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e4e7ed;
}

.panel-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.panel-body {
  flex: 1;
  overflow: auto;
  padding: 16px;
}

.process-list {
  height: 100%;
}

.process-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

:deep(.el-table__body tr.current-row > td) {
  background-color: #ecf5ff !important;
}

:deep(.el-table__row) {
  cursor: pointer;
}
</style>
