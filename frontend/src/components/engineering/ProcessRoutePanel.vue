<template>
  <div class="process-route-panel">
    <!-- 面板标题 -->
    <div class="panel-header">
      <h3>工艺路线编排</h3>
      <div class="header-actions">
        <template v-if="processRoutes.length > 0">
          <el-button 
            type="primary" 
            size="small"
            :disabled="!canCreateRoute"
            @click="handleCreateRoute"
          >
            新建工艺路线
          </el-button>
          <el-button 
            type="success" 
            size="small"
            :disabled="!canAddProcess"
            @click="handleAddProcess"
          >
            + 添加标准工序
          </el-button>
        </template>
      </div>
    </div>
    
    <div v-if="hasSelectedBomNode && selectedBomNode?.node_type === 'PART' && processRoutes.length > 0" class="route-selector">
      <el-select
        v-model="selectedRouteId"
        placeholder="选择工艺路线"
        style="width: 100%"
        @change="handleRouteChange"
      >
        <el-option
          v-for="route in processRoutes"
          :key="route.id"
          :label="route.route_name"
          :value="route.id"
        >
          <div class="route-option">
            <span>{{ route.route_name }}</span>
            <el-tag size="small" type="info">{{ route.route_code }}</el-tag>
          </div>
        </el-option>
      </el-select>
    </div>
    
    <div class="panel-body">
      <el-empty 
        v-if="!hasSelectedBomNode"
        description="请先在左侧选择一个零件节点"
        :image-size="120"
      />
      
      <el-empty 
        v-else-if="selectedBomNode?.node_type === 'ASSEMBLY'"
        description="装配节点无法配置工艺路线，请选择叶子零件节点"
        :image-size="120"
      />
      
      <el-empty 
        v-else-if="!routesLoading && processRoutes.length === 0"
        :image-size="120"
      >
        <template #description>
          <p class="empty-description">该零件尚未配置工艺路线</p>
          <p class="empty-hint">点击下方按钮，快速添加首道工序</p>
        </template>
        <el-button 
          type="primary" 
          size="large"
          :icon="Plus"
          :disabled="!isCurrentVersionEditable"
          @click="handleAddFirstProcess"
        >
          + 添加首道标准工序
        </el-button>
      </el-empty>
      
      <el-empty 
        v-else-if="!selectedRouteId"
        description="请选择一条工艺路线"
        :image-size="120"
      />
      
      <div v-else class="process-list">
        <el-table
          v-loading="routesLoading || stepsLoading"
          :data="routeSteps"
          highlight-current-row
          @current-change="handleCurrentChange"
          @row-click="handleRowClick"
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
                :disabled="!isCurrentVersionEditable || $index === 0"
                @click="handleMoveUp($index)"
              >
                上移
              </el-button>
              <el-button 
                link 
                type="primary" 
                size="small"
                :disabled="!isCurrentVersionEditable || $index === routeSteps.length - 1"
                @click="handleMoveDown($index)"
              >
                下移
              </el-button>
              <el-button 
                link 
                type="danger" 
                size="small"
                :disabled="!isCurrentVersionEditable"
                @click="handleDelete(row)"
              >
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        
        <el-empty 
          v-if="!routesLoading && !stepsLoading && routeSteps.length === 0"
          description="暂无工序，请点击上方按钮添加标准工序"
          :image-size="100"
        />
      </div>
    </div>
    
    <ProcessSelectorDialog 
      v-model="selectorVisible"
      @select="handleProcessSelect"
    />
    
    <el-dialog
      v-model="createRouteVisible"
      title="新建工艺路线"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="routeFormRef"
        :model="routeForm"
        :rules="routeRules"
        label-width="100px"
      >
        <el-form-item label="路线名称" prop="route_name">
          <el-input 
            v-model="routeForm.route_name" 
            placeholder="请输入路线名称"
            maxlength="100"
          />
        </el-form-item>
        
        <el-form-item label="路线编码" prop="route_code">
          <el-input 
            v-model="routeForm.route_code" 
            placeholder="请输入路线编码"
            maxlength="50"
          />
        </el-form-item>
        
        <el-form-item label="描述" prop="description">
          <el-input 
            v-model="routeForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入描述"
            maxlength="512"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="createRouteVisible = false">取消</el-button>
        <el-button type="primary" :loading="createRouteLoading" :disabled="!isCurrentVersionEditable" @click="handleCreateRouteSubmit">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import { useEngineeringStore } from '@/stores/engineering'
import type { RouteStepBindWithProcess } from '@/api/engineering'
import ProcessSelectorDialog from './ProcessSelectorDialog.vue'

const store = useEngineeringStore()

const hasSelectedBomNode = computed(() => store.hasSelectedBomNode)
const selectedBomNode = computed(() => store.selectedBomNode)
const processRoutes = computed(() => store.processRoutes)
const routeSteps = computed(() => store.routeSteps)
const routesLoading = computed(() => store.routesLoading)
const stepsLoading = computed(() => store.stepsLoading)
const selectedRoute = computed(() => store.selectedRoute)
const isCurrentVersionEditable = computed(() => store.isCurrentVersionEditable)

const selectedRouteId = ref<number | null>(null)
const isFirstProcess = ref(false)

const canCreateRoute = computed(() => {
  return hasSelectedBomNode.value && selectedBomNode.value?.node_type === 'PART' && isCurrentVersionEditable.value
})

const canAddProcess = computed(() => {
  return canCreateRoute.value && selectedRouteId.value !== null
})

watch(selectedRoute, (newRoute) => {
  selectedRouteId.value = newRoute?.id ?? null
})

watch(processRoutes, (routes) => {
  if (routes.length > 0 && !selectedRouteId.value) {
    selectedRouteId.value = routes[0].id
    const route = routes.find(r => r.id === selectedRouteId.value)
    if (route) {
      store.selectRoute(route)
    }
  }
})

function handleRouteChange(routeId: number) {
  const route = processRoutes.value.find(r => r.id === routeId)
  if (route) {
    store.selectRoute(route)
  }
}

const selectorVisible = ref(false)

const createRouteVisible = ref(false)
const createRouteLoading = ref(false)
const routeFormRef = ref<FormInstance>()
const routeForm = ref({
  route_name: '',
  route_code: '',
  description: '',
})

const routeRules: FormRules = {
  route_name: [
    { required: true, message: '请输入路线名称', trigger: 'blur' },
    { min: 1, max: 100, message: '长度在 1 到 100 个字符', trigger: 'blur' },
  ],
  route_code: [
    { required: true, message: '请输入路线编码', trigger: 'blur' },
    { min: 1, max: 50, message: '长度在 1 到 50 个字符', trigger: 'blur' },
    { pattern: /^[A-Za-z0-9_-]+$/, message: '只能包含字母、数字、下划线和横杠', trigger: 'blur' },
  ],
}

function handleCurrentChange(currentRow: RouteStepBindWithProcess | null) {
  store.selectStep(currentRow)
}

function handleRowClick(row: RouteStepBindWithProcess) {
  store.selectStep(row)
}

function handleAddProcess() {
  if (!isCurrentVersionEditable.value) {
    return
  }

  isFirstProcess.value = false
  selectorVisible.value = true
}

function handleAddFirstProcess() {
  if (!isCurrentVersionEditable.value) {
    return
  }

  isFirstProcess.value = true
  selectorVisible.value = true
}

async function handleProcessSelect(processId: number) {
  try {
    if (isFirstProcess.value) {
      await store.addFirstProcessWithDefaultRoute(processId)
    } else {
      await store.addRouteStep(processId)
    }
    selectorVisible.value = false
    isFirstProcess.value = false
  } catch (error) {
    console.error('Process select failed:', error)
  }
}

function handleCreateRoute() {
  if (!isCurrentVersionEditable.value) {
    return
  }

  routeForm.value = {
    route_name: '',
    route_code: '',
    description: '',
  }
  createRouteVisible.value = true
}

async function handleCreateRouteSubmit() {
  if (!isCurrentVersionEditable.value) {
    return
  }

  if (!routeFormRef.value) return
  
  try {
    await routeFormRef.value.validate()
    
    createRouteLoading.value = true
    
    const result = await store.createProcessRoute({
      route_name: routeForm.value.route_name,
      route_code: routeForm.value.route_code,
      description: routeForm.value.description || null,
    })
    
    if (result) {
      createRouteVisible.value = false
      selectedRouteId.value = result.id
    }
  } catch (error) {
    console.error('Create route failed:', error)
  } finally {
    createRouteLoading.value = false
  }
}

async function handleMoveUp(index: number) {
  if (!isCurrentVersionEditable.value) {
    return
  }

  if (index === 0) return
  
  const newSteps = [...routeSteps.value]
  const temp = newSteps[index - 1]
  newSteps[index - 1] = newSteps[index]
  newSteps[index] = temp
  
  const stepIds = newSteps.map(step => step.id)
  await store.reorderRouteSteps(stepIds)
}

async function handleMoveDown(index: number) {
  if (!isCurrentVersionEditable.value) {
    return
  }

  if (index === routeSteps.value.length - 1) return
  
  const newSteps = [...routeSteps.value]
  const temp = newSteps[index + 1]
  newSteps[index + 1] = newSteps[index]
  newSteps[index] = temp
  
  const stepIds = newSteps.map(step => step.id)
  await store.reorderRouteSteps(stepIds)
}

async function handleDelete(row: RouteStepBindWithProcess) {
  if (!isCurrentVersionEditable.value) {
    return
  }

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

.header-actions {
  display: flex;
  gap: 8px;
}

.route-selector {
  padding: 12px 16px;
  border-bottom: 1px solid #e4e7ed;
  background-color: #fafafa;
}

.route-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
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

.empty-description {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.empty-hint {
  font-size: 12px;
  color: #c0c4cc;
  margin-bottom: 16px;
}

:deep(.el-table__body tr.current-row > td) {
  background-color: #ecf5ff !important;
}

:deep(.el-table__row) {
  cursor: pointer;
}
</style>
