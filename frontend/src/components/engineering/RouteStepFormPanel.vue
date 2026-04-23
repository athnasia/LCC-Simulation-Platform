<template>
  <div class="route-step-form-panel">
    <div class="panel-header">
      <h3>资源参数覆写</h3>
    </div>
    
    <div class="panel-body">
      <el-empty 
        v-if="!selectedStep"
        description="请在中栏选择一个工序步骤"
        :image-size="120"
      />
      
      <el-form 
        v-else
        ref="formRef"
        :model="form"
        label-width="100px"
        label-position="right"
        v-loading="loading"
      >
        <el-divider content-position="left">
          <el-text type="info">基础信息（只读）</el-text>
        </el-divider>
        
        <el-form-item label="工序名称">
          <el-input :value="selectedStep.process?.name || '-'" disabled />
        </el-form-item>
        
        <el-form-item label="工序编码">
          <el-input :value="selectedStep.process?.code || '-'" disabled />
        </el-form-item>
        
        <el-divider content-position="left">
          <el-text type="info">加工设置</el-text>
        </el-divider>
        
        <el-form-item label="加工方式">
          <el-radio-group v-model="form.process_type" @change="handleProcessTypeChange">
            <el-radio value="IN_HOUSE">
              <el-icon><OfficeBuilding /></el-icon>
              厂内自制
            </el-radio>
            <el-radio value="OUTSOURCED">
              <el-icon><Van /></el-icon>
              委外加工
            </el-radio>
          </el-radio-group>
        </el-form-item>
        
        <template v-if="form.process_type === 'IN_HOUSE'">
          <el-form-item label="覆写设备">
            <el-select
              v-model="form.override_equipment_id"
              placeholder="留空则使用标准默认设备"
              clearable
              filterable
              style="width: 100%"
            >
              <el-option
                v-for="equipment in equipmentOptions"
                :key="equipment.id"
                :label="equipment.name"
                :value="equipment.id"
              >
                <div class="equipment-option">
                  <span>{{ equipment.name }}</span>
                  <el-tag size="small" type="info">{{ equipment.code }}</el-tag>
                </div>
              </el-option>
            </el-select>
          </el-form-item>
          
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
        </template>
        
        <template v-else-if="form.process_type === 'OUTSOURCED'">
          <el-divider content-position="left">
            <el-text type="info">外协价格</el-text>
          </el-divider>
          
          <el-form-item label="外协单价">
            <el-input-number
              v-model="form.outsource_price"
              :min="0"
              :precision="2"
              :step="10"
              placeholder="请输入外协单价"
              style="width: 100%"
            />
            <el-text size="small" type="info">
              单位：元/件
            </el-text>
          </el-form-item>
        </template>
        
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
import { OfficeBuilding, Van } from '@element-plus/icons-vue'
import type { FormInstance } from 'element-plus'
import { useEngineeringStore } from '@/stores/engineering'
import type { RouteStepBindWithProcess } from '@/api/engineering'

interface MaterialItem {
  code: string
  name: string
  quantity: number | null
  unit?: string
}

interface EquipmentOption {
  id: number
  code: string
  name: string
}

const store = useEngineeringStore()

const selectedStep = computed(() => store.selectedStep)

const formRef = ref<FormInstance>()
const loading = ref(false)
const saving = ref(false)

const form = ref({
  process_type: 'IN_HOUSE' as 'IN_HOUSE' | 'OUTSOURCED',
  override_equipment_id: null as number | null,
  outsource_price: null as number | null,
  override_t_set: null as number | null,
  override_t_run: null as number | null,
  description: '',
})

const materialList = ref<MaterialItem[]>([])

const equipmentOptions = ref<EquipmentOption[]>([
  { id: 1, code: 'EQ_CNC_001', name: '数控车床 A' },
  { id: 2, code: 'EQ_CNC_002', name: '数控车床 B' },
  { id: 3, code: 'EQ_MILL_001', name: '立式铣床' },
  { id: 4, code: 'EQ_DRILL_001', name: '摇臂钻床' },
  { id: 5, code: 'EQ_GRIND_001', name: '平面磨床' },
])

watch(selectedStep, (newStep) => {
  if (newStep) {
    form.value = {
      process_type: newStep.process_type || 'IN_HOUSE',
      override_equipment_id: newStep.override_equipment_id,
      outsource_price: newStep.outsource_price,
      override_t_set: newStep.override_t_set,
      override_t_run: newStep.override_t_run,
      description: newStep.description || '',
    }
    
    if (newStep.override_mat_params) {
      materialList.value = Object.entries(newStep.override_mat_params).map(([code, quantity]) => ({
        code,
        name: getMaterialName(code),
        quantity: quantity as number,
        unit: getMaterialUnit(code),
      }))
    } else {
      loadStandardMaterials(newStep)
    }
  } else {
    form.value = {
      process_type: 'IN_HOUSE',
      override_equipment_id: null,
      outsource_price: null,
      override_t_set: null,
      override_t_run: null,
      description: '',
    }
    materialList.value = []
  }
}, { immediate: true })

function handleProcessTypeChange() {
  if (form.value.process_type === 'IN_HOUSE') {
    form.value.outsource_price = null
  } else {
    form.value.override_equipment_id = null
    form.value.override_t_set = null
    form.value.override_t_run = null
  }
}

function getMaterialName(code: string): string {
  const materialNames: Record<string, string> = {
    'MAT_CUTTING_FLUID': '切削液',
    'MAT_COPPER_INGOT': '铜锭',
    'MAT_STEEL_PLATE': '钢板',
    'MAT_LUBRICANT': '润滑油',
  }
  return materialNames[code] || code
}

function getMaterialUnit(code: string): string {
  const materialUnits: Record<string, string> = {
    'MAT_CUTTING_FLUID': 'L',
    'MAT_COPPER_INGOT': 'kg',
    'MAT_STEEL_PLATE': 'kg',
    'MAT_LUBRICANT': 'L',
  }
  return materialUnits[code] || '件'
}

async function loadStandardMaterials(step: RouteStepBindWithProcess) {
  loading.value = true
  try {
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

async function handleSave() {
  if (!selectedStep.value) {
    ElMessage.warning('请先选择工序步骤')
    return
  }
  
  saving.value = true
  try {
    const materialParams = buildMaterialParams()
    
    await store.updateRouteStep(selectedStep.value.id, {
      process_type: form.value.process_type,
      override_equipment_id: form.value.override_equipment_id,
      outsource_price: form.value.outsource_price,
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

.equipment-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
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

:deep(.el-radio-group) {
  display: flex;
  gap: 16px;
}

:deep(.el-radio) {
  display: flex;
  align-items: center;
  gap: 4px;
}
</style>
