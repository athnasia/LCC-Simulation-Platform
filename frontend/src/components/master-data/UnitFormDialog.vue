<template>
  <el-dialog
    v-model="visible"
    :title="isEdit ? '编辑单位' : '新建单位'"
    width="620px"
    :close-on-click-modal="false"
    @closed="resetForm"
  >
    <el-alert
      v-if="selectedDimension"
      type="info"
      :closable="false"
      class="mb-4"
    >
      <template #title>
        当前量纲：{{ selectedDimension.name }}（{{ selectedDimension.code }}）
      </template>
    </el-alert>

    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="108px"
    >
      <el-form-item label="单位名称" prop="name">
        <el-input v-model="form.name" maxlength="50" placeholder="例如：米、千克、小时" />
      </el-form-item>
      <el-form-item label="单位编码" prop="code">
        <el-input
          v-model="form.code"
          maxlength="20"
          placeholder="例如：m、kg、hour"
          :disabled="isEdit"
        />
      </el-form-item>
      <el-form-item label="单位符号" prop="symbol">
        <el-input v-model="form.symbol" maxlength="10" placeholder="例如：m、kg、h" />
      </el-form-item>
      <el-form-item label="单位类型" prop="is_base">
        <el-radio-group v-model="form.is_base" :disabled="isEdit">
          <el-radio :value="true">基准单位</el-radio>
          <el-radio :value="false">转换单位</el-radio>
        </el-radio-group>
        <div v-if="isEdit" class="mt-2 text-xs text-gray-500">
          为避免换算链路漂移，编辑时不开放类型切换。
        </div>
      </el-form-item>

      <el-form-item v-if="!form.is_base" label="换算系数" prop="conversion_factor">
        <el-input-number
          v-model="form.conversion_factor"
          :min="0.000001"
          :precision="6"
          controls-position="right"
          class="w-full"
          placeholder="请输入相对基准单位的线性换算系数"
        />
        <div class="mt-2 text-xs text-gray-500">
          {{ conversionHint }}
        </div>
      </el-form-item>

      <el-form-item label="描述" prop="description">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="3"
          maxlength="256"
          show-word-limit
          placeholder="请输入单位说明"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="handleSubmit">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { unitApi, unitConversionApi } from '@/api/masterData'
import type {
  Unit,
  UnitConversion,
  UnitCreate,
  UnitDimension,
  UnitUpdate,
  UnitConversionCreate,
  UnitConversionUpdate,
} from '@/api/masterData'

interface UnitFormModel {
  name: string
  code: string
  symbol: string
  is_base: boolean
  conversion_factor: number | null
  description: string
}

const props = defineProps<{
  modelValue: boolean
  data?: Unit | null
  selectedDimension: UnitDimension | null
  baseUnit: Unit | null
  conversions: UnitConversion[]
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'success'): void
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (value: boolean) => emit('update:modelValue', value),
})

const isEdit = computed(() => Boolean(props.data?.id))
const submitting = ref(false)
const formRef = ref<FormInstance>()
const form = reactive<UnitFormModel>({
  name: '',
  code: '',
  symbol: '',
  is_base: false,
  conversion_factor: null,
  description: '',
})

const rules: FormRules<UnitFormModel> = {
  name: [
    { required: true, message: '请输入单位名称', trigger: 'blur' },
    { min: 1, max: 50, message: '单位名称长度为 1-50 个字符', trigger: 'blur' },
  ],
  code: [
    { required: true, message: '请输入单位编码', trigger: 'blur' },
    { pattern: /^[a-zA-Z][a-zA-Z0-9_]*$/, message: '单位编码必须以英文开头，仅包含字母、数字和下划线', trigger: 'blur' },
  ],
  conversion_factor: [
    {
      validator: (_rule, value: number | null, callback) => {
        if (form.is_base) {
          callback()
          return
        }
        if (value === null || Number.isNaN(value) || value <= 0) {
          callback(new Error('转换单位必须填写大于 0 的换算系数'))
          return
        }
        callback()
      },
      trigger: 'change',
    },
  ],
}

const conversionHint = computed(() => {
  if (form.is_base) {
    return '基准单位无需维护换算系数。'
  }
  if (!props.baseUnit) {
    return '请先在当前量纲下创建一个基准单位，再维护转换单位。'
  }
  const baseSymbol = props.baseUnit.symbol || props.baseUnit.code
  const currentSymbol = form.symbol.trim() || form.code.trim() || '当前单位'
  return `当前页面仅支持线性换算，系统将按“1 ${currentSymbol} = X ${baseSymbol}”写入换算规则，offset 固定为 0。`
})

watch(
  () => props.modelValue,
  (opened: boolean) => {
    if (opened) {
      hydrateForm()
    }
  },
)

function hydrateForm() {
  if (props.data) {
    form.name = props.data.name
    form.code = props.data.code
    form.symbol = props.data.symbol ?? ''
    form.is_base = props.data.is_base
    form.description = props.data.description ?? ''
    form.conversion_factor = resolveConversionFactor(props.data)
    return
  }

  form.name = ''
  form.code = ''
  form.symbol = ''
  form.is_base = props.baseUnit === null
  form.conversion_factor = props.baseUnit === null ? 1 : null
  form.description = ''
}

function resetForm() {
  formRef.value?.clearValidate()
  form.name = ''
  form.code = ''
  form.symbol = ''
  form.is_base = false
  form.conversion_factor = null
  form.description = ''
}

function normalizeText(value: string): string | null {
  const trimmed = value.trim()
  return trimmed.length > 0 ? trimmed : null
}

function getRelatedConversion(unitId: number): UnitConversion | null {
  const baseUnit = props.baseUnit
  if (!baseUnit || baseUnit.id === unitId) {
    return null
  }

  return (
    props.conversions.find(
      (item: UnitConversion) => item.from_unit.id === unitId && item.to_unit.id === baseUnit.id,
    ) ??
    props.conversions.find(
      (item: UnitConversion) => item.from_unit.id === baseUnit.id && item.to_unit.id === unitId,
    ) ??
    null
  )
}

function resolveConversionFactor(unit: Unit): number | null {
  if (unit.is_base) {
    return 1
  }
  const relation = getRelatedConversion(unit.id)
  if (!relation || !props.baseUnit) {
    return null
  }
  const factor = Number(relation.conversion_factor)
  if (relation.from_unit.id === unit.id && relation.to_unit.id === props.baseUnit.id) {
    return factor
  }
  return factor > 0 ? 1 / factor : null
}

async function upsertConversion(unitId: number) {
  if (form.is_base) {
    return
  }

  if (!props.baseUnit) {
    throw new Error('当前量纲尚未存在基准单位，无法创建转换单位')
  }

  const factor = form.conversion_factor
  if (factor === null || factor <= 0) {
    throw new Error('转换系数必须大于 0')
  }

  const description = `1 ${form.symbol.trim() || form.code.trim()} = ${factor} ${props.baseUnit.symbol || props.baseUnit.code}`
  const relation = getRelatedConversion(unitId)

  if (!relation) {
    const payload: UnitConversionCreate = {
      from_unit_id: unitId,
      to_unit_id: props.baseUnit.id,
      conversion_factor: factor,
      offset: 0,
      description,
    }
    await unitConversionApi.create(payload)
    return
  }

  if (relation.from_unit.id === unitId && relation.to_unit.id === props.baseUnit.id) {
    const payload: UnitConversionUpdate = {
      conversion_factor: factor,
      offset: 0,
      description,
    }
    await unitConversionApi.update(relation.id, payload)
    return
  }

  const payload: UnitConversionUpdate = {
    conversion_factor: 1 / factor,
    offset: 0,
    description,
  }
  await unitConversionApi.update(relation.id, payload)
}

async function handleSubmit() {
  if (!props.selectedDimension) {
    ElMessage.warning('请先选择一个量纲')
    return
  }

  if (!isEdit.value && form.is_base && props.baseUnit) {
    ElMessage.warning('当前量纲已存在基准单位，请直接维护现有基准单位')
    return
  }

  if (!form.is_base && !props.baseUnit) {
    ElMessage.warning('请先创建基准单位，再维护转换单位')
    return
  }

  const validated = await formRef.value?.validate().then(() => true).catch(() => false)
  if (!validated) {
    return
  }

  submitting.value = true
  try {
    let unitId = props.data?.id ?? 0

    if (isEdit.value && props.data) {
      const payload: UnitUpdate = {
        name: form.name.trim(),
        symbol: normalizeText(form.symbol),
        is_base: form.is_base,
        description: normalizeText(form.description),
      }
      const response = await unitApi.update(props.data.id, payload)
      unitId = response.data.id
      ElMessage.success('单位已更新')
    } else {
      const payload: UnitCreate = {
        name: form.name.trim(),
        code: form.code.trim(),
        symbol: normalizeText(form.symbol),
        dimension_id: props.selectedDimension.id,
        is_base: form.is_base,
        description: normalizeText(form.description),
      }
      const response = await unitApi.create(payload)
      unitId = response.data.id
      ElMessage.success('单位已创建')
    }

    await upsertConversion(unitId)
    visible.value = false
    emit('success')
  } catch {
    // 请求失败提示由全局拦截器统一处理
  } finally {
    submitting.value = false
  }
}
</script>