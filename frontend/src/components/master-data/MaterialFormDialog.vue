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
          <el-input
            v-model="attr.key"
            placeholder="属性名（英文标识）"
            class="attr-key"
            @change="updateDynamicAttributes"
          />
          <el-input
            v-model="attr.value"
            placeholder="属性值"
            class="attr-value"
            @change="updateDynamicAttributes"
          />
          <el-button
            type="danger"
            :icon="Delete"
            circle
            @click="removeAttr(index)"
          />
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
import { materialApi, unitApi } from '@/api/masterData'
import type { Material, ResourceCategoryTree, Unit } from '@/api/masterData'

interface DynamicAttr {
  key: string
  value: string
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
const dynamicAttrs = ref<DynamicAttr[]>([])

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
  return filterCategoryTree(props.categoryTree, 'MATERIAL')
})

function filterCategoryTree(tree: ResourceCategoryTree[], resourceType: string): ResourceCategoryTree[] {
  return tree
    .filter((node) => node.resource_type === resourceType)
    .map((node) => ({
      ...node,
      children: node.children ? filterCategoryTree(node.children, resourceType) : [],
    }))
}

async function loadUnits() {
  const res = await unitApi.list({ size: 200, is_active: true })
  unitOptions.value = res.data.items
}

function parseDynamicAttributes(attrs: Record<string, unknown> | null) {
  if (!attrs) return []
  return Object.entries(attrs).map(([key, value]) => ({
    key,
    value: String(value),
  }))
}

function updateDynamicAttributes() {
  const result: Record<string, unknown> = {}
  for (const attr of dynamicAttrs.value) {
    if (attr.key.trim()) {
      const numValue = Number(attr.value)
      result[attr.key.trim()] = isNaN(numValue) ? attr.value : numValue
    }
  }
  form.dynamic_attributes = Object.keys(result).length > 0 ? result : null
}

function addAttr() {
  dynamicAttrs.value.push({ key: '', value: '' })
}

function removeAttr(index: number) {
  dynamicAttrs.value.splice(index, 1)
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
  (val) => {
    if (val && unitOptions.value.length === 0) {
      loadUnits()
    }
  },
)

async function handleSubmit() {
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

.attr-key {
  width: 180px;
}

.attr-value {
  flex: 1;
}
</style>
