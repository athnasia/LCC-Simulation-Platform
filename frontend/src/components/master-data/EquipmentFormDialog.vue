<template>
  <el-dialog
    v-model="visible"
    :title="isEdit ? '编辑设备' : '新建设备'"
    width="760px"
    :close-on-click-modal="false"
    @closed="resetForm"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="110px"
      size="default"
    >
      <!-- ── 基础信息 ────────────────────────────────────── -->
      <el-divider content-position="left">基础信息</el-divider>

      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="设备名称" prop="name">
            <el-input v-model="form.name" placeholder="请输入设备名称" maxlength="100" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="设备编码" prop="code">
            <el-input
              v-model="form.code"
              placeholder="请输入设备编码"
              maxlength="50"
              :disabled="isEdit"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="设备分类" prop="category_id">
            <el-tree-select
              v-model="form.category_id"
              :data="categoryTreeData"
              :props="{ value: 'id', label: 'name', children: 'children' }"
              placeholder="请选择设备分类"
              clearable
              check-strictly
              class="w-full"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="启用状态" prop="is_active">
            <el-switch v-model="form.is_active" active-text="启用" inactive-text="禁用" />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="折旧费率" prop="depreciation_rate">
            <el-input-number
              v-model="form.depreciation_rate"
              :precision="4"
              :min="0"
              placeholder="元/小时"
              controls-position="right"
              class="w-full"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="能耗系数" prop="power_consumption">
            <el-input-number
              v-model="form.power_consumption"
              :precision="4"
              :min="0"
              placeholder="kW/h"
              controls-position="right"
              class="w-full"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="换型成本" prop="setup_cost">
            <el-input-number
              v-model="form.setup_cost"
              :precision="2"
              :min="0"
              placeholder="元/次"
              controls-position="right"
              class="w-full"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="目标 OEE" prop="oee_target">
            <el-input-number
              v-model="form.oee_target"
              :precision="2"
              :min="0"
              :max="100"
              placeholder="%"
              controls-position="right"
              class="w-full"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="MTBF" prop="mtbf_hours">
            <el-input-number
              v-model="form.mtbf_hours"
              :precision="2"
              :min="0"
              placeholder="小时"
              controls-position="right"
              class="w-full"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="缺陷率" prop="defect_rate">
            <el-input-number
              v-model="form.defect_rate"
              :precision="4"
              :min="0"
              :max="100"
              placeholder="%"
              controls-position="right"
              class="w-full"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item label="描述" prop="description">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="2"
          placeholder="请输入设备描述"
          maxlength="512"
          show-word-limit
        />
      </el-form-item>

      <!-- ── 柔性属性（动态渲染）─────────────────────────── -->
      <el-divider content-position="left">扩展属性（动态键值对）</el-divider>

      <div class="dynamic-attrs-container">
        <div v-for="(attr, index) in dynamicAttrs" :key="index" class="attr-row">
          <el-form-item
            :prop="`dynamic_attr_${index}`"
            :rules="[{ validator: validateAttrKey, trigger: 'blur' }]"
            class="attr-key-form-item"
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
                v-for="def in equipmentAttrDefs"
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
        <el-button type="primary" link :icon="Plus" @click="addAttr">
          添加属性
        </el-button>
      </div>
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
import { attrDefinitionApi, equipmentApi, ResourceType } from '@/api/masterData'
import type { AttrDataType, AttrDefinition, Equipment, ResourceCategoryTree } from '@/api/masterData'
import { ATTR_DATA_TYPE_OPTIONS } from '@/constants/systemDictionaries'
import { useDictionaryStore } from '@/stores/dictionaries'
import { resolveDictionaryInputHint } from '@/utils/dictionaryDisplay'

interface DynamicAttr {
  key: string
  value: string
  hasError: boolean
}

const props = defineProps<{
  modelValue: boolean
  data?: Equipment | null
  categoryTree: ResourceCategoryTree[]
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
const dynamicAttrs = ref<DynamicAttr[]>([])
const equipmentAttrDefs = ref<AttrDefinition[]>([])
const attrDefMap = ref<Map<string, AttrDefinition>>(new Map())
const dictionaryStore = useDictionaryStore()
const attrDataTypeOptions = computed(() => dictionaryStore.getOptions('ATTR_DATA_TYPE', ATTR_DATA_TYPE_OPTIONS))

const form = reactive({
  name: '',
  code: '',
  category_id: null as number | null,
  depreciation_rate: null as number | null,
  power_consumption: null as number | null,
  setup_cost: null as number | null,
  oee_target: null as number | null,
  mtbf_hours: null as number | null,
  defect_rate: null as number | null,
  dynamic_attributes: null as Record<string, unknown> | null,
  is_active: true,
  description: null as string | null,
})

const rules = computed<FormRules>(() => ({
  name: [
    { required: true, message: '请输入设备名称', trigger: 'blur' },
    { min: 1, max: 100, message: '设备名称长度 1-100', trigger: 'blur' },
  ],
  code: [
    { required: true, message: '请输入设备编码', trigger: 'blur' },
    { min: 1, max: 50, message: '设备编码长度 1-50', trigger: 'blur' },
  ],
}))

const categoryTreeData = computed(() => {
  return filterCategoryTree(props.categoryTree, ResourceType.EQUIPMENT)
})

function filterCategoryTree(tree: ResourceCategoryTree[], resourceType: string): ResourceCategoryTree[] {
  return tree
    .filter((node) => node.resource_type === resourceType)
    .map((node) => ({
      ...node,
      children: node.children ? filterCategoryTree(node.children, resourceType) : [],
    }))
}

// ── 属性模板加载 ──────────────────────────────────────────

async function loadEquipmentAttrDefs() {
  try {
    const res = await attrDefinitionApi.list({ size: 100 })
    const allDefs = res.data.items
    equipmentAttrDefs.value = allDefs.filter(
      (def) => def.applicable_resource_types?.includes(ResourceType.EQUIPMENT)
    )
    attrDefMap.value = new Map(equipmentAttrDefs.value.map((def) => [def.code, def]))
  } catch {
    equipmentAttrDefs.value = []
    attrDefMap.value = new Map()
  }
}

// ── 柔性属性逻辑 ──────────────────────────────────────────

function parseDynamicAttributes(attrs: Record<string, unknown> | null) {
  if (!attrs) return []
  return Object.entries(attrs).map(([key, value]) => ({
    key,
    value: String(value),
    hasError: false,
  }))
}

function getAttrDataType(key: string): AttrDataType | null {
  const def = attrDefMap.value.get(key)
  return def?.data_type ?? null
}

function getAttrValuePlaceholder(key: string): string {
  const def = attrDefMap.value.get(key)
  if (!def) return '属性值'
  if (def.data_type === 'ENUM' && def.enum_values?.length) {
    return def.enum_values.join(' / ')
  }
  return resolveDictionaryInputHint(attrDataTypeOptions.value, def.data_type, '属性值')
}

function convertValueByType(value: string, dataType: AttrDataType): unknown {
  if (!value.trim()) return value

  switch (dataType) {
    case 'NUMBER': {
      const num = Number(value)
      return isNaN(num) ? value : num
    }
    case 'BOOLEAN': {
      if (value.toLowerCase() === 'true') return true
      if (value.toLowerCase() === 'false') return false
      return value
    }
    case 'JSON': {
      try {
        return JSON.parse(value)
      } catch {
        return value
      }
    }
    case 'DATE': {
      const dateRegex = /^\d{4}-\d{2}-\d{2}$/
      if (dateRegex.test(value)) return value
      return value
    }
    case 'ENUM':
    case 'STRING':
    default:
      return value
  }
}

function validateAttrKey(_rule: unknown, value: string, callback: (error?: Error) => void) {
  if (!value || !value.trim()) {
    callback()
    return
  }
  const trimmedKey = value.trim()
  const count = dynamicAttrs.value.filter((attr) => attr.key.trim() === trimmedKey).length
  if (count > 1) {
    callback(new Error('键名重复'))
  } else {
    callback()
  }
}

function checkDuplicateKeys() {
  const keyCount = new Map<string, number>()
  dynamicAttrs.value.forEach((attr) => {
    const key = attr.key.trim()
    if (key) {
      keyCount.set(key, (keyCount.get(key) ?? 0) + 1)
    }
  })

  dynamicAttrs.value.forEach((attr) => {
    const key = attr.key.trim()
    attr.hasError = (keyCount.get(key) ?? 0) > 1
  })
}

function onAttrKeyChange() {
  checkDuplicateKeys()
  updateDynamicAttributes()
}

function updateDynamicAttributes() {
  checkDuplicateKeys()

  const hasErrors = dynamicAttrs.value.some((attr) => attr.hasError)
  if (hasErrors) {
    form.dynamic_attributes = null
    return
  }

  const result: Record<string, unknown> = {}
  for (const attr of dynamicAttrs.value) {
    const key = attr.key.trim()
    if (key && attr.value.trim()) {
      const dataType = getAttrDataType(key)
      if (dataType) {
        result[key] = convertValueByType(attr.value, dataType)
      } else {
        result[key] = attr.value
      }
    }
  }
  form.dynamic_attributes = Object.keys(result).length > 0 ? result : null
}

function addAttr() {
  dynamicAttrs.value.push({ key: '', value: '', hasError: false })
}

function removeAttr(index: number) {
  dynamicAttrs.value.splice(index, 1)
  checkDuplicateKeys()
  updateDynamicAttributes()
}

// ── 数据回填与弹窗生命周期 ─────────────────────────────────

watch(
  () => props.data,
  (equipment) => {
    if (equipment) {
      form.name = equipment.name
      form.code = equipment.code
      form.category_id = equipment.category_id
      form.depreciation_rate = equipment.depreciation_rate
      form.power_consumption = equipment.power_consumption
      form.setup_cost = equipment.setup_cost
      form.oee_target = equipment.oee_target
      form.mtbf_hours = equipment.mtbf_hours
      form.defect_rate = equipment.defect_rate
      form.dynamic_attributes = equipment.dynamic_attributes
      form.is_active = equipment.is_active
      form.description = equipment.description
      dynamicAttrs.value = parseDynamicAttributes(equipment.dynamic_attributes)
    } else {
      dynamicAttrs.value = []
    }
  },
  { immediate: true },
)

watch(
  () => props.modelValue,
  async (val) => {
    if (val) {
      await dictionaryStore.ensureLoaded().catch(() => undefined)
      if (equipmentAttrDefs.value.length === 0) {
        loadEquipmentAttrDefs()
      }
    }
  },
)

// ── 提交 ──────────────────────────────────────────────────

async function handleSubmit() {
  const hasDuplicateKeys = dynamicAttrs.value.some((attr) => attr.hasError)
  if (hasDuplicateKeys) {
    ElMessage.error('存在重复的属性键名，请修正后再提交')
    return
  }

  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    const payload = {
      name: form.name,
      code: form.code,
      category_id: form.category_id,
      depreciation_rate: form.depreciation_rate,
      power_consumption: form.power_consumption,
      setup_cost: form.setup_cost,
      oee_target: form.oee_target,
      mtbf_hours: form.mtbf_hours,
      defect_rate: form.defect_rate,
      dynamic_attributes: form.dynamic_attributes,
      is_active: form.is_active,
      description: form.description,
    }

    if (isEdit.value && props.data?.id) {
      await equipmentApi.update(props.data.id, payload)
      ElMessage.success('更新成功')
    } else {
      await equipmentApi.create(payload)
      ElMessage.success('创建成功')
    }
    emit('success')
    visible.value = false
  } finally {
    loading.value = false
  }
}

function resetForm() {
  formRef.value?.resetFields()
  form.category_id = null
  form.depreciation_rate = null
  form.power_consumption = null
  form.setup_cost = null
  form.oee_target = null
  form.mtbf_hours = null
  form.defect_rate = null
  form.dynamic_attributes = null
  form.is_active = true
  form.description = null
  dynamicAttrs.value = []
}
</script>

<style scoped>
.dynamic-attrs-container {
  padding: 0 12px;
}

.attr-row {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
  align-items: center;
}

.attr-key-form-item {
  margin-bottom: 0;
}

.attr-key {
  width: 180px;
}

.attr-value {
  flex: 1;
}

.attr-code-hint {
  color: #909399;
  font-size: 12px;
  margin-left: 4px;
}

.error-hint {
  color: #f56c6c;
  font-size: 12px;
  white-space: nowrap;
}

.attr-value.is-error :deep(.el-input__wrapper) {
  box-shadow: 0 0 0 1px #f56c6c inset;
}
</style>
