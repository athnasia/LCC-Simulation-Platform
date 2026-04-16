<template>
  <div class="route-step-form-panel">
    <!-- 面板标题 -->
    <div class="panel-header">
      <h3>资源参数覆写</h3>
    </div>
    
    <!-- 内容区域 -->
    <div class="panel-body">
      <!-- 空状态：未选中工序 -->
      <el-empty 
        v-if="!selectedStep"
        description="请在中栏选择一个工序步骤"
        :image-size="120"
      />
      
      <!-- 表单 -->
      <el-form 
        v-else
        ref="formRef"
        :model="form"
        label-width="100px"
        label-position="right"
        v-loading="loading"
      >
        <!-- 基础信息（只读） -->
        <el-divider content-position="left">
          <el-text type="info">基础信息（只读）</el-text>
        </el-divider>
        
        <el-form-item label="工序名称">
          <el-input :value="selectedStep.process?.name || '-'" disabled />
        </el-form-item>
        
        <el-form-item label="工序编码">
          <el-input :value="selectedStep.process?.code || '-'" disabled />
        </el-form-item>
        
        <!-- 工时覆写 -->
        <el-divider content-position="left">
          <el-text type="info">工时覆写</el-text>
        </el-divider>
        
        <el-form-item label="准备工时">
          <el-input-number
            v-model="form.override_t_set"
            :min="0"
            :precision="4"
            :step="0.1"
            placeholder="请输入准备工时"
            style="width: 100%"
          />
          <el-text v-if="selectedStep.process?.setup_time" size="small" type="info">
            标准值: {{ selectedStep.process.setup_time }} h
          </el-text>
        </el-form-item>
        
        <el-form-item label="运行工时">
          <el-input-number
            v-model="form.override_t_run"
            :min="0"
            :precision="4"
            :step="0.1"
            placeholder="请输入运行工时"
            style="width: 100%"
          />
          <el-text v-if="selectedStep.process?.standard_time" size="small" type="info">
            标准值: {{ selectedStep.process.standard_time }} h
          </el-text>
        </el-form-item>
        
        <!-- 辅材消耗覆写 -->
        <el-divider content-position="left">
          <el-text type="info">辅材消耗覆写</el-text>
        </el-divider>
        
        <div class="material-params">
          <div 
            v-for="(material, index) in materialList" 
            :key="index"
            class="material-item"
          >
            <div class="material-info">
              <span class="material-name">{{ material.name }}</span>
              <el-tag size="small" type="info">{{ material.code }}</el-tag>
            </div>
            <div class="material-input">
              <el-input-number
                v-model="material.quantity"
                :min="0"
                :precision="4"
                :step="0.1"
                placeholder="请输入消耗量"
                style="width: 150px"
              />
              <span class="unit">{{ material.unit || '件' }}</span>
            </div>
          </div>
          
          <el-empty 
            v-if="materialList.length === 0"
            description="该工序暂无标准材料清单"
            :image-size="80"
          />
        </div>
        
        <!-- 描述 -->
        <el-divider content-position="left">
          <el-text type="info">备注</el-text>
        </el-divider>
        
        <el-form-item label="描述">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入备注信息"
            maxlength="512"
            show-word-limit
          />
        </el-form-item>
        
        <!-- 保存按钮 -->
        <el-form-item>
          <el-button 
            type="primary" 
            :loading="saving"
            @click="handleSave"
          >
            保存参数
          </el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance } from 'element-plus'
import { useEngineeringStore } from '@/stores/engineering'
import type { RouteStepBindWithProcess } from '@/api/engineering'

interface MaterialItem {
  code: string
  name: string
  quantity: number | null
  unit?: string
}

const store = useEngineeringStore()

// 从 Store 获取状态
const selectedStep = computed(() => store.selectedStep)

// 表单引用
const formRef = ref<FormInstance>()
const loading = ref(false)
const saving = ref(false)

// 表单数据
const form = ref({
  override_t_set: null as number | null,
  override_t_run: null as number | null,
  description: '',
})

// 材料列表
const materialList = ref<MaterialItem[]>([])

// 监听选中的工序步骤变化
watch(selectedStep, (newStep) => {
  if (newStep) {
    // 填充表单数据
    form.value = {
      override_t_set: newStep.override_t_set,
      override_t_run: newStep.override_t_run,
      description: newStep.description || '',
    }
    
    // 解析材料参数
    if (newStep.override_mat_params) {
      materialList.value = Object.entries(newStep.override_mat_params).map(([code, quantity]) => ({
        code,
        name: getMaterialName(code),
        quantity: quantity as number,
        unit: getMaterialUnit(code),
      }))
    } else {
      // 从标准工艺中获取材料清单（这里需要根据实际业务逻辑调整）
      loadStandardMaterials(newStep)
    }
  } else {
    // 清空表单
    form.value = {
      override_t_set: null,
      override_t_run: null,
      description: '',
    }
    materialList.value = []
  }
}, { immediate: true })

// 获取材料名称（模拟数据）
function getMaterialName(code: string): string {
  const materialNames: Record<string, string> = {
    'MAT_CUTTING_FLUID': '切削液',
    'MAT_COPPER_INGOT': '铜锭',
    'MAT_STEEL_PLATE': '钢板',
    'MAT_LUBRICANT': '润滑油',
  }
  return materialNames[code] || code
}

// 获取材料单位（模拟数据）
function getMaterialUnit(code: string): string {
  const materialUnits: Record<string, string> = {
    'MAT_CUTTING_FLUID': 'L',
    'MAT_COPPER_INGOT': 'kg',
    'MAT_STEEL_PLATE': 'kg',
    'MAT_LUBRICANT': 'L',
  }
  return materialUnits[code] || '件'
}

// 加载标准材料清单（模拟数据）
async function loadStandardMaterials(step: RouteStepBindWithProcess) {
  loading.value = true
  try {
    // 这里应该从后端获取标准工艺的材料清单
    // 暂时使用模拟数据
    await new Promise(resolve => setTimeout(resolve, 300))
    
    materialList.value = [
      { code: 'MAT_CUTTING_FLUID', name: '切削液', quantity: null, unit: 'L' },
      { code: 'MAT_COPPER_INGOT', name: '铜锭', quantity: null, unit: 'kg' },
    ]
  } catch (error) {
    console.error('Failed to load standard materials:', error)
  } finally {
    loading.value = false
  }
}

// 组装材料参数 JSON
function buildMaterialParams(): Record<string, number> | null {
  const validMaterials = materialList.value.filter(m => m.quantity !== null && m.quantity > 0)
  
  if (validMaterials.length === 0) {
    return null
  }
  
  const result: Record<string, number> = {}
  validMaterials.forEach(material => {
    result[material.code] = material.quantity!
  })
  
  return result
}

// 保存参数
async function handleSave() {
  if (!selectedStep.value) {
    ElMessage.warning('请先选择工序步骤')
    return
  }
  
  saving.value = true
  try {
    const materialParams = buildMaterialParams()
    
    await store.updateRouteStep(selectedStep.value.id, {
      override_t_set: form.value.override_t_set,
      override_t_run: form.value.override_t_run,
      override_mat_params: materialParams,
      description: form.value.description || null,
    })
    
    ElMessage.success('保存成功')
  } catch (error) {
    console.error('Save failed:', error)
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.route-step-form-panel {
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

.material-params {
  padding: 0 20px;
}

.material-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.material-item:last-child {
  border-bottom: none;
}

.material-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.material-name {
  font-weight: 500;
  color: #303133;
}

.material-input {
  display: flex;
  align-items: center;
  gap: 8px;
}

.unit {
  color: #909399;
  font-size: 14px;
}

:deep(.el-divider__text) {
  background-color: #fff;
  padding: 0 10px;
}

:deep(.el-form-item) {
  margin-bottom: 18px;
}

:deep(.el-text) {
  display: block;
  margin-top: 4px;
}
</style>
