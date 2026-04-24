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

      <div v-else-if="!isCurrentVersionEditable" class="readonly-banner">
        当前方案版本已发布，资源参数覆写仅可查看，不能修改。
      </div>
      
      <el-form 
        v-if="selectedStep"
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
          <el-radio-group v-model="form.process_type" :disabled="!isCurrentVersionEditable" @change="handleProcessTypeChange">
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
              :disabled="!isCurrentVersionEditable"
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
              :disabled="!isCurrentVersionEditable"
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
              :disabled="!isCurrentVersionEditable"
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
              :disabled="!isCurrentVersionEditable"
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
                :disabled="!isCurrentVersionEditable"
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
            :disabled="!isCurrentVersionEditable"
            maxlength="512"
            show-word-limit
          />
        </el-form-item>
        
        <el-form-item>
          <el-button 
            type="primary" 
            :loading="saving"
            :disabled="!isCurrentVersionEditable"
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
import { useEngineeringStore } from '@/stores/engineering'
import type { RouteStepBindWithProcess } from '@/api/engineering'
import { materialApi, processApi, type Material } from '@/api/masterData'

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
const isCurrentVersionEditable = computed(() => store.isCurrentVersionEditable)

const loading = ref(false)
const saving = ref(false)
const materialDetailCache = new Map<number, Material>()
let materialLoadToken = 0

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
      outsource_price: toNumberOrNull(newStep.outsource_price),
      override_t_set: toNumberOrNull(newStep.override_t_set),
      override_t_run: toNumberOrNull(newStep.override_t_run),
      description: newStep.description || '',
    }

    void loadProcessMaterials(newStep)
  } else {
    materialLoadToken += 1
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

function toNumberOrNull(value: unknown): number | null {
  if (value === null || value === undefined || value === '') {
    return null
  }

  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : null
}

function handleProcessTypeChange() {
  if (form.value.process_type === 'IN_HOUSE') {
    form.value.outsource_price = null
  } else {
    form.value.override_equipment_id = null
    form.value.override_t_set = null
    form.value.override_t_run = null
  }
}

async function loadProcessMaterials(step: RouteStepBindWithProcess) {
  const token = ++materialLoadToken
  loading.value = true
  try {
    const processRes = await processApi.detail(step.process.id)
    const materialResources = processRes.data.resources.filter((resource) => resource.resource_type === 'MATERIAL')
    const overrideMap = step.override_mat_params || {}

    if (materialResources.length === 0) {
      if (token === materialLoadToken) {
        materialList.value = []
      }
      return
    }

    const materials = await Promise.all(
      materialResources.map(async (resource) => {
        const cached = materialDetailCache.get(resource.resource_id)
        if (cached) {
          return cached
        }

        const detail = await materialApi.detail(resource.resource_id)
        materialDetailCache.set(resource.resource_id, detail.data)
        return detail.data
      }),
    )

    if (token === materialLoadToken) {
      materialList.value = materials.map((material) => ({
        code: material.code,
        name: material.name,
        quantity: toNumberOrNull(overrideMap[material.code]),
        unit: material.consumption_unit?.symbol || material.consumption_unit?.name || material.pricing_unit?.symbol || material.pricing_unit?.name || '件',
      }))
    }
  } catch (error) {
    console.error('Failed to load process materials:', error)
    if (token === materialLoadToken) {
      materialList.value = []
    }
  } finally {
    if (token === materialLoadToken) {
      loading.value = false
    }
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
  if (!isCurrentVersionEditable.value) {
    return
  }

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

.readonly-banner {
  margin-bottom: 16px;
  padding: 12px 14px;
  border-radius: 8px;
  color: #8a5a00;
  background-color: #fff7e6;
  border: 1px solid #f5d39c;
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
