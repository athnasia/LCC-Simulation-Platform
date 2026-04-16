<template>
  <el-dialog
    v-model="visible"
    :title="isEdit ? '编辑标准工艺' : '新建工艺'"
    width="900px"
    destroy-on-close
    :close-on-click-modal="false"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="100px"
      v-loading="loading"
    >
      <!-- ── 基础信息 ────────────────────────────── -->
      <div class="font-medium mb-4 text-gray-700">基础信息</div>
      
      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="工序编码" prop="code">
            <el-input
              v-model="form.code"
              placeholder="请输入字母/数字/下划线"
              :disabled="isEdit"
              maxlength="50"
              show-word-limit
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="工序名称" prop="name">
            <el-input
              v-model="form.name"
              placeholder="请输入工序名称"
              maxlength="100"
              show-word-limit
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="工序分类" prop="category_id">
            <el-tree-select
              v-model="form.category_id"
              :data="categoryTree"
              node-key="id"
              :props="{ label: 'name', children: 'children' }"
              check-strictly
              filterable
              clearable
              placeholder="请选择工序分类"
              class="w-full"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="状态" prop="is_active">
            <el-switch
              v-model="form.is_active"
              active-text="启用"
              inactive-text="禁用"
              inline-prompt
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="准备工时" prop="setup_time">
            <el-input-number
              v-model="form.setup_time"
              :precision="4"
              :min="0"
              placeholder="h"
              controls-position="right"
              class="w-full"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="标准工时" prop="standard_time">
            <el-input-number
              v-model="form.standard_time"
              :precision="4"
              :min="0"
              placeholder="h"
              controls-position="right"
              class="w-full"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item label="工序描述" prop="description">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="2"
          placeholder="请输入工序的说明与描述"
          maxlength="512"
          show-word-limit
        />
      </el-form-item>

      <!-- ── 资源挂载 ────────────────────────────── -->
      <div class="font-medium mt-6 mb-4 text-gray-700">资源编排与挂载</div>
      
      <el-tabs v-model="activeTab" type="border-card" class="shadow-none">
        <!-- 柔性属性 -->
        <el-tab-pane label="扩展属性" name="ATTRIBUTES">
          <div class="dynamic-attrs-container">
            <div v-for="(attr, index) in dynamicAttrs" :key="index" class="attr-row">
              <el-form-item
                :prop="`dynamic_attr_${index}`"
                :rules="[{ validator: validateAttrKey, trigger: 'blur' }]"
                class="attr-key-form-item"
                label-width="0"
              >
                <el-select
                  v-model="attr.key"
                  placeholder="选择或输入属性"
                  filterable
                  allow-create
                  default-first-option
                  class="attr-key"
                  @change="onAttrKeyChange"
                >
                  <el-option
                    v-for="def in processAttrDefs"
                    :key="def.code"
                    :label="def.name"
                    :value="def.code"
                  >
                    <span>{{ def.name }}</span>
                    <span class="attr-code-hint">（{{ def.code }}）</span>
                  </el-option>
                </el-select>
              </el-form-item>
              <el-input
                v-model="attr.value"
                :placeholder="getAttrValuePlaceholder(attr.key)"
                class="attr-value"
                :class="{ 'is-error': attr.hasError }"
                @change="updateDynamicAttributes"
              />
              <el-button
                type="danger"
                :icon="Delete"
                circle
                @click="removeAttr(index)"
              />
              <span v-if="attr.hasError" class="error-hint">键名重复</span>
            </div>
            <el-button type="primary" link :icon="Plus" @click="addAttr" class="mt-2 text-sm">
              添加属性
            </el-button>
          </div>
        </el-tab-pane>

        <!-- 材料清单 -->
        <el-tab-pane label="材料清单" name="MATERIAL">
          <div class="mb-2">
            <el-button size="small" type="primary" :icon="Plus" @click="addResource('MATERIAL')">添加消耗材料</el-button>
          </div>
          <el-table :data="mountedMaterials" size="small" border>
            <el-table-column label="选择材料" min-width="200">
              <template #default="{ row }">
                <el-select v-model="row.resource_id" filterable placeholder="选择材料" class="w-full">
                  <el-option v-for="item in materialOptions" :key="item.id" :label="`${item.name} (${item.code})`" :value="item.id" />
                </el-select>
              </template>
            </el-table-column>
            <el-table-column label="消耗数量" width="140">
              <template #default="{ row }">
                <el-input-number v-model="row.quantity" :min="0.0001" :precision="4" controls-position="right" class="w-full" />
              </template>
            </el-table-column>
            <el-table-column label="备注说明" min-width="150">
              <template #default="{ row }">
                <el-input v-model="row.description" placeholder="配比、要求等" maxlength="100" />
              </template>
            </el-table-column>
            <el-table-column label="操作" width="70" align="center">
              <template #default="{ $index }">
                <el-button size="small" type="danger" link @click="mountedMaterials.splice($index, 1)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- 使用设备 -->
        <el-tab-pane label="使用设备" name="EQUIPMENT">
          <div class="mb-2">
            <el-button size="small" type="primary" :icon="Plus" @click="addResource('EQUIPMENT')">添加关联设备</el-button>
          </div>
          <el-table :data="mountedEquipments" size="small" border>
            <el-table-column label="选择设备" min-width="200">
              <template #default="{ row }">
                <el-select v-model="row.resource_id" filterable placeholder="选择设备" class="w-full">
                  <el-option v-for="item in equipmentOptions" :key="item.id" :label="`${item.name} (${item.code})`" :value="item.id" />
                </el-select>
              </template>
            </el-table-column>
            <el-table-column label="占线比例/数量" width="140">
              <template #default="{ row }">
                <el-input-number v-model="row.quantity" :min="0.0001" :precision="4" controls-position="right" class="w-full" />
              </template>
            </el-table-column>
            <el-table-column label="关联说明" min-width="150">
              <template #default="{ row }">
                <el-input v-model="row.description" placeholder="辅机要求等" maxlength="100" />
              </template>
            </el-table-column>
            <el-table-column label="操作" width="70" align="center">
              <template #default="{ $index }">
                <el-button size="small" type="danger" link @click="mountedEquipments.splice($index, 1)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- 指派人员 -->
        <el-tab-pane label="指派人员" name="LABOR">
          <div class="mb-2">
            <el-button size="small" type="primary" :icon="Plus" @click="addResource('LABOR')">指派人员/工种</el-button>
          </div>
          <el-table :data="mountedLabors" size="small" border>
            <el-table-column label="选择人员矩阵" min-width="200">
              <template #default="{ row }">
                <el-select v-model="row.resource_id" filterable placeholder="选择人员" class="w-full">
                  <el-option v-for="item in laborOptions" :key="item.id" :label="`${item.name} (${item.code})`" :value="item.id" />
                </el-select>
              </template>
            </el-table-column>
            <el-table-column label="投入系数" width="140">
              <template #default="{ row }">
                <el-input-number v-model="row.quantity" :min="0.0001" :precision="4" controls-position="right" class="w-full" />
              </template>
            </el-table-column>
            <el-table-column label="指派说明" min-width="150">
              <template #default="{ row }">
                <el-input v-model="row.description" placeholder="职责要求" maxlength="100" />
              </template>
            </el-table-column>
            <el-table-column label="操作" width="70" align="center">
              <template #default="{ $index }">
                <el-button size="small" type="danger" link @click="mountedLabors.splice($index, 1)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>

    </el-form>

    <template #footer>
      <el-button @click="visible = false">取 消</el-button>
      <el-button type="primary" :loading="loading" @click="handleSubmit">确 定</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Delete } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'

import { attrDefinitionApi, processApi, materialApi, equipmentApi, laborApi, ResourceType } from '@/api/masterData'
import type { AttrDefinition, Process, ResourceCategory, Material, Equipment, Labor, ProcessResource } from '@/api/masterData'
import { ATTR_DATA_TYPE_OPTIONS } from '@/constants/systemDictionaries'
import { useDictionaryStore } from '@/stores/dictionaries'
import { resolveDictionaryInputHint } from '@/utils/dictionaryDisplay'

interface DynamicAttr {
  key: string
  value: string
  hasError: boolean
}

type LocalProcessResource = {
  id?: number
  resource_type: string
  resource_id: number | null
  quantity: number
  description: string | null
}

const props = defineProps<{
  modelValue: boolean
  data?: Process | null
  categoryTree: ResourceCategory[]
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', val: boolean): void
  (e: 'success'): void
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

const isEdit = computed(() => !!props.data?.id)
const loading = ref(false)
const formRef = ref<FormInstance>()
const activeTab = ref('ATTRIBUTES')

// Attribute Dictionaries
const dynamicAttrs = ref<DynamicAttr[]>([])
const processAttrDefs = ref<AttrDefinition[]>([])
const attrDefMap = ref<Map<string, AttrDefinition>>(new Map())
const dictionaryStore = useDictionaryStore()
const attrDataTypeOptions = computed(() => dictionaryStore.getOptions('ATTR_DATA_TYPE', ATTR_DATA_TYPE_OPTIONS))

// Resources Lookup Options
const materialOptions = ref<Material[]>([])
const equipmentOptions = ref<Equipment[]>([])
const laborOptions = ref<Labor[]>([])

// Mounted Resources
const mountedMaterials = ref<LocalProcessResource[]>([])
const mountedEquipments = ref<LocalProcessResource[]>([])
const mountedLabors = ref<LocalProcessResource[]>([])

const form = reactive({
  code: '',
  name: '',
  category_id: null as number | null,
  setup_time: null as number | null,
  standard_time: null as number | null,
  dynamic_attributes: {} as Record<string, string | number | boolean>,
  is_active: true,
  description: '' as string | null
})

const rules: FormRules = {
  code: [
    { required: true, message: '请输入工序编码', trigger: 'blur' },
    { pattern: /^[A-Za-z0-9_]+$/, message: '编码只能包含字母、数字和下划线', trigger: 'blur' }
  ],
  name: [
    { required: true, message: '请输入工序名称', trigger: 'blur' }
  ]
}

async function loadLookupOptions() {
  try {
    const [matRes, eqRes, labRes] = await Promise.all([
      materialApi.list({ page: 1, size: 500, is_active: true }),
      equipmentApi.list({ page: 1, size: 500, is_active: true }),
      laborApi.list({ page: 1, size: 500, is_active: true })
    ])
    materialOptions.value = matRes.data.items || []
    equipmentOptions.value = eqRes.data.items || []
    laborOptions.value = labRes.data.items || []
  } catch (error) {
    console.error('Failed to load lookup options:', error)
  }
}

async function loadAttrDefs() {
  try {
    const res = await attrDefinitionApi.list({ 
      page: 1, 
      size: 500, 
      resource_type: ResourceType.PROCESS 
    })
    processAttrDefs.value = res.data.items || []
    attrDefMap.value.clear()
    processAttrDefs.value.forEach(def => {
      attrDefMap.value.set(def.code, def)
    })
  } catch (error) {
    console.error('Failed to load process attributes:', error)
  }
}

function getAttrValuePlaceholder(code: string): string {
  if (!code) return '输入属性值'
  const def = attrDefMap.value.get(code)
  if (!def) return '输入属性值'
  return resolveDictionaryInputHint(def, attrDataTypeOptions.value)
}

function onAttrKeyChange() {
  updateDynamicAttributes()
}

function validateAttrKey(rule: any, value: any, callback: any) {
  const index = parseInt(rule.field.split('_')[2])
  const currentAttr = dynamicAttrs.value[index]
  if (!currentAttr.key) {
    callback()
    return
  }
  
  const isDuplicate = dynamicAttrs.value.some((attr, i) => i !== index && attr.key === currentAttr.key)
  currentAttr.hasError = isDuplicate
  
  if (isDuplicate) {
    callback(new Error('键名重复'))
  } else {
    callback()
  }
}

function addAttr() {
  dynamicAttrs.value.push({ key: '', value: '', hasError: false })
}

function removeAttr(index: number) {
  dynamicAttrs.value.splice(index, 1)
  updateDynamicAttributes()
}

function updateDynamicAttributes() {
  const attrs: Record<string, any> = {}
  dynamicAttrs.value.forEach(attr => {
    if (attr.key && attr.value !== '' && !attr.hasError) {
      if (!isNaN(Number(attr.value)) && attr.value.trim() !== '') {
        attrs[attr.key] = Number(attr.value)
      } else if (attr.value.toLowerCase() === 'true') {
        attrs[attr.key] = true
      } else if (attr.value.toLowerCase() === 'false') {
        attrs[attr.key] = false
      } else {
        attrs[attr.key] = attr.value
      }
    }
  })
  form.dynamic_attributes = attrs
}

function addResource(type: string) {
  const blank: LocalProcessResource = {
    resource_type: type,
    resource_id: null,
    quantity: 1,
    description: null
  }
  if (type === 'MATERIAL') mountedMaterials.value.push(blank)
  if (type === 'EQUIPMENT') mountedEquipments.value.push(blank)
  if (type === 'LABOR') mountedLabors.value.push(blank)
}

watch(visible, async (val) => {
  if (val) {
    activeTab.value = 'ATTRIBUTES'
    if (processAttrDefs.value.length === 0) await loadAttrDefs()
    if (materialOptions.value.length === 0) await loadLookupOptions()
    
    if (formRef.value) formRef.value.resetFields()
    
    dynamicAttrs.value = []
    mountedMaterials.value = []
    mountedEquipments.value = []
    mountedLabors.value = []
    
    if (isEdit.value && props.data) {
      Object.assign(form, {
        code: props.data.code,
        name: props.data.name,
        category_id: props.data.category_id,
        setup_time: props.data.setup_time,
        standard_time: props.data.standard_time,
        dynamic_attributes: { ...(props.data.dynamic_attributes || {}) },
        is_active: props.data.is_active,
        description: props.data.description
      })
      
      if (props.data.dynamic_attributes) {
        Object.entries(props.data.dynamic_attributes).forEach(([key, value]) => {
          dynamicAttrs.value.push({ key, value: String(value), hasError: false })
        })
      }

      // Distribute resources into tabs based on resource_type
      if (props.data.resources && Array.isArray(props.data.resources)) {
        props.data.resources.forEach(r => {
          const item = {
            id: r.id,
            resource_type: r.resource_type,
            resource_id: r.resource_id,
            quantity: r.quantity,
            description: r.description
          }
          if (r.resource_type === 'MATERIAL') mountedMaterials.value.push(item)
          if (r.resource_type === 'EQUIPMENT') mountedEquipments.value.push(item)
          if (r.resource_type === 'LABOR') mountedLabors.value.push(item)
        })
      }
    } else {
      Object.assign(form, {
        code: '',
        name: '',
        category_id: null,
        setup_time: null,
        standard_time: null,
        dynamic_attributes: {},
        is_active: true,
        description: null
      })
    }
  }
})

async function handleSubmit() {
  if (!formRef.value) return
  
  const hasErrors = dynamicAttrs.value.some(attr => attr.hasError)
  if (hasErrors) {
    ElMessage.warning('请修复重复的属性键名')
    activeTab.value = 'ATTRIBUTES'
    return
  }

  // Gather all valid resources from tabs
  const allResources = [...mountedMaterials.value, ...mountedEquipments.value, ...mountedLabors.value]
  
  // Basic validation: ensure all selected resources have a resource_id
  const hasIncompleteResource = allResources.some(row => !row.resource_id)
  if (hasIncompleteResource) {
    ElMessage.warning('请为所有添加的挂载项目选择具体资源，或者将其删除')
    return
  }

  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    loading.value = true
    try {
      updateDynamicAttributes()
      
      if (isEdit.value) {
        // Edit flow: Update base properties first
        const payload = {
          name: form.name,
          category_id: form.category_id,
          setup_time: form.setup_time,
          standard_time: form.standard_time,
          dynamic_attributes: Object.keys(form.dynamic_attributes).length > 0 ? form.dynamic_attributes : null,
          is_active: form.is_active,
          description: form.description || null
        }
        await processApi.update(props.data!.id, payload)
        
        // Sync Resources with rollback protection
        const processId = props.data!.id
        const originalResources = props.data!.resources || []
        
        // Calculate diffs
        const toRemoveIds: number[] = []
        const toAdd: LocalProcessResource[] = []
        
        for (const orig of originalResources) {
          const stillExists = allResources.find(r => r.id === orig.id)
          if (!stillExists || String(stillExists.quantity) !== String(orig.quantity) || stillExists.description !== orig.description) {
            toRemoveIds.push(orig.id)
          }
        }
        
        for (const curr of allResources) {
          const orig = originalResources.find(r => r.id === curr.id)
          if (!orig || String(curr.quantity) !== String(orig.quantity) || curr.description !== orig.description) {
            toAdd.push(curr)
          }
        }
        
        // Execute resource sync: batch remove first, then batch add
        try {
          // 1. Remove obsolete or changed resources (Logical deletion is handled by Service)
          if (toRemoveIds.length > 0) {
            await Promise.all(
              toRemoveIds.map(id => processApi.removeResource(processId, id))
            )
          }
          // 2. Add new resources
          if (toAdd.length > 0) {
            await Promise.all(
              toAdd.map(curr => processApi.addResource(processId, {
                resource_type: curr.resource_type as ResourceType,
                resource_id: curr.resource_id!,
                quantity: curr.quantity,
                description: curr.description
              }))
            )
          }
        } catch (syncError) {
          console.error('Resource sync partially failed:', syncError)
          ElMessage.warning('工艺基础信息已保存，但部分资源挂载同步失败，请刷新并重新确认资源状态')
          emit('success')
          return
        }
        
        ElMessage.success('更新工艺成功')
      } else {
        // Create flow: Attach directly to payload
        const payload = {
          name: form.name,
          code: form.code,
          category_id: form.category_id,
          setup_time: form.setup_time,
          standard_time: form.standard_time,
          dynamic_attributes: Object.keys(form.dynamic_attributes).length > 0 ? form.dynamic_attributes : null,
          is_active: form.is_active,
          description: form.description || null,
          resources: allResources.map(r => ({
            resource_type: r.resource_type as 'MATERIAL' | 'EQUIPMENT' | 'LABOR' | 'TOOL',
            resource_id: r.resource_id!,
            quantity: r.quantity,
            description: r.description
          }))
        }
        await processApi.create(payload)
        ElMessage.success('创建工艺成功')
      }
      
      visible.value = false
      emit('success')
    } catch (error) {
      console.error('Submit failed:', error)
    } finally {
      loading.value = false
    }
  })
}
</script>

<style scoped>
.dynamic-attrs-container {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px 0;
}

.attr-row {
  display: flex;
  gap: 8px;
  align-items: flex-start;
  position: relative;
}

.attr-key-form-item {
  margin-bottom: 0 !important;
  width: 200px;
}

.attr-key {
  width: 100%;
}

.attr-value {
  flex: 1;
}

.error-hint {
  position: absolute;
  top: 32px;
  left: 0;
  font-size: 12px;
  color: var(--el-color-danger);
}

.is-error :deep(.el-input__wrapper) {
  box-shadow: 0 0 0 1px var(--el-color-danger) inset !important;
}

.attr-code-hint {
  color: var(--el-text-color-secondary);
  font-size: 12px;
  margin-left: 4px;
}
</style>
