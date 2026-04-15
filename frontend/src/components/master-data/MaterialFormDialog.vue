<template>
  <el-dialog
    v-model="visible"
    :title="isEdit ? '编辑材料' : '新建材料'"
    width="720px"
    :close-on-click-modal="false"
    @closed="resetForm"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="100px"
      size="default"
    >
      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="材料名称" prop="name">
            <el-input v-model="form.name" placeholder="请输入材料名称" maxlength="100" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="材料编码" prop="code">
            <el-input
              v-model="form.code"
              placeholder="请输入材料编码"
              maxlength="50"
              :disabled="isEdit"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="材料分类" prop="category_id">
            <el-tree-select
              v-model="form.category_id"
              :data="categoryTreeData"
              :props="{ value: 'id', label: 'name', children: 'children' }"
              placeholder="请选择材料分类"
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
          <el-form-item label="计价单位" prop="pricing_unit_id">
            <el-select
              v-model="form.pricing_unit_id"
              placeholder="请选择计价单位"
              clearable
              filterable
              remote
              :remote-method="searchUnits"
              :loading="unitLoading"
              class="w-full"
            >
              <el-option
                v-for="unit in unitOptions"
                :key="unit.id"
                :label="`${unit.name} (${unit.symbol})`"
                :value="unit.id"
              />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="消耗单位" prop="consumption_unit_id">
            <el-select
              v-model="form.consumption_unit_id"
              placeholder="请选择消耗单位"
              clearable
              filterable
              remote
              :remote-method="searchUnits"
              :loading="unitLoading"
              class="w-full"
            >
              <el-option
                v-for="unit in unitOptions"
                :key="unit.id"
                :label="`${unit.name} (${unit.symbol})`"
                :value="unit.id"
              />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="单价" prop="unit_price">
            <el-input-number
              v-model="form.unit_price"
              :precision="4"
              :min="0"
              placeholder="元/计价单位"
              controls-position="right"
              class="w-full"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="损耗率" prop="loss_rate">
            <el-input-number
              v-model="form.loss_rate"
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
          <el-form-item label="废料残值" prop="scrap_value">
            <el-input-number
              v-model="form.scrap_value"
              :precision="4"
              :min="0"
              placeholder="元/单位"
              controls-position="right"
              class="w-full"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="替代料群组" prop="substitute_group">
            <el-input v-model="form.substitute_group" placeholder="同组材料可互换" maxlength="50" />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="替代优先级" prop="substitute_priority">
            <el-input-number
              v-model="form.substitute_priority"
              :min="1"
              placeholder="数字越小优先级越高"
              controls-position="right"
              class="w-full"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="疲劳寿命" prop="lcc_lifespan_months">
            <el-input-number
              v-model="form.lcc_lifespan_months"
              :min="1"
              placeholder="月"
              controls-position="right"
              class="w-full"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item label="维保成本" prop="lcc_maintenance_cost">
        <el-input-number
          v-model="form.lcc_maintenance_cost"
          :precision="2"
          :min="0"
          placeholder="单次维保预估成本（元）"
          controls-position="right"
          class="w-full"
        />
      </el-form-item>

      <el-form-item label="描述" prop="description">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="2"
          placeholder="请输入材料描述"
          maxlength="512"
          show-word-limit
        />
      </el-form-item>

      <el-divider content-position="left">柔性属性（动态键值对）</el-divider>

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
                v-for="def in materialAttrDefs"
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
import { attrDefinitionApi, materialApi, ResourceType, unitApi } from '@/api/masterData'
import type { AttrDataType, AttrDefinition, Material, ResourceCategoryTree, Unit } from '@/api/masterData'
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
  data?: Material | null
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
const unitOptions = ref<Unit[]>([])
const unitLoading = ref(false)
const dynamicAttrs = ref<DynamicAttr[]>([])
const materialAttrDefs = ref<AttrDefinition[]>([])
const attrDefMap = ref<Map<string, AttrDefinition>>(new Map())
const dictionaryStore = useDictionaryStore()
const attrDataTypeOptions = computed(() => dictionaryStore.getOptions('ATTR_DATA_TYPE', ATTR_DATA_TYPE_OPTIONS))

const form = reactive({
  name: '',
  code: '',
  category_id: null as number | null,
  pricing_unit_id: null as number | null,
  consumption_unit_id: null as number | null,
  unit_price: null as number | null,
  loss_rate: null as number | null,
  scrap_value: null as number | null,
  substitute_group: null as string | null,
  substitute_priority: null as number | null,
  lcc_lifespan_months: null as number | null,
  lcc_maintenance_cost: null as number | null,
  dynamic_attributes: null as Record<string, unknown> | null,
  is_active: true,
  description: null as string | null,
})

const rules = computed<FormRules>(() => ({
  name: [
    { required: true, message: '请输入材料名称', trigger: 'blur' },
    { min: 1, max: 100, message: '材料名称长度 1-100', trigger: 'blur' },
  ],
  code: [
    { required: true, message: '请输入材料编码', trigger: 'blur' },
    { min: 1, max: 50, message: '材料编码长度 1-50', trigger: 'blur' },
  ],
}))

const categoryTreeData = computed(() => {
  return filterCategoryTree(props.categoryTree, ResourceType.MATERIAL)
})

function filterCategoryTree(tree: ResourceCategoryTree[], resourceType: ResourceType): ResourceCategoryTree[] {
  return tree
    .filter((node) => node.resource_type === resourceType)
    .map((node) => ({
      ...node,
      children: node.children ? filterCategoryTree(node.children, resourceType) : [],
    }))
}

async function loadUnits(keyword?: string) {
  unitLoading.value = true
  try {
    const res = await unitApi.list({ size: 50, is_active: true, keyword })
    unitOptions.value = res.data.items
  } finally {
    unitLoading.value = false
  }
}

function searchUnits(keyword: string) {
  loadUnits(keyword)
}

async function loadMaterialAttrDefs() {
  try {
    const res = await attrDefinitionApi.list({ size: 100 })
    const allDefs = res.data.items
    materialAttrDefs.value = allDefs.filter(
      (def) => def.applicable_resource_types?.includes(ResourceType.MATERIAL)
    )
    attrDefMap.value = new Map(materialAttrDefs.value.map((def) => [def.code, def]))
  } catch {
    materialAttrDefs.value = []
    attrDefMap.value = new Map()
  }
}

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
    attr.hasError = keyCount.get(key)! > 1
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

watch(
  () => props.data,
  (material) => {
    if (material) {
      form.name = material.name
      form.code = material.code
      form.category_id = material.category_id
      form.pricing_unit_id = material.pricing_unit_id
      form.consumption_unit_id = material.consumption_unit_id
      form.unit_price = material.unit_price
      form.loss_rate = material.loss_rate
      form.scrap_value = material.scrap_value
      form.substitute_group = material.substitute_group
      form.substitute_priority = material.substitute_priority
      form.lcc_lifespan_months = material.lcc_lifespan_months
      form.lcc_maintenance_cost = material.lcc_maintenance_cost
      form.dynamic_attributes = material.dynamic_attributes
      form.is_active = material.is_active
      form.description = material.description
      dynamicAttrs.value = parseDynamicAttributes(material.dynamic_attributes)
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
      if (unitOptions.value.length === 0) {
        loadUnits()
      }
      if (materialAttrDefs.value.length === 0) {
        loadMaterialAttrDefs()
      }
    }
  },
)

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
      pricing_unit_id: form.pricing_unit_id,
      consumption_unit_id: form.consumption_unit_id,
      unit_price: form.unit_price,
      loss_rate: form.loss_rate,
      scrap_value: form.scrap_value,
      substitute_group: form.substitute_group,
      substitute_priority: form.substitute_priority,
      lcc_lifespan_months: form.lcc_lifespan_months,
      lcc_maintenance_cost: form.lcc_maintenance_cost,
      dynamic_attributes: form.dynamic_attributes,
      is_active: form.is_active,
      description: form.description,
    }

    if (isEdit.value && props.data?.id) {
      await materialApi.update(props.data.id, payload)
      ElMessage.success('更新成功')
    } else {
      await materialApi.create(payload)
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
  form.pricing_unit_id = null
  form.consumption_unit_id = null
  form.unit_price = null
  form.loss_rate = null
  form.scrap_value = null
  form.substitute_group = null
  form.substitute_priority = null
  form.lcc_lifespan_months = null
  form.lcc_maintenance_cost = null
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
