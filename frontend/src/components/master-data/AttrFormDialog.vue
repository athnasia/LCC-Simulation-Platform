<template>
  <el-dialog
    v-model="visible"
    :title="isEdit ? '编辑柔性属性' : '新建柔性属性'"
    width="680px"
    :close-on-click-modal="false"
    @closed="resetForm"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="110px"
    >
      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="属性名称" prop="name">
            <el-input v-model="form.name" maxlength="50" placeholder="例如：密度、硬度、能效比" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="属性编码" prop="code">
            <el-input
              v-model="form.code"
              maxlength="30"
              placeholder="例如：density"
              :disabled="isEdit"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="数据类型" prop="data_type">
            <el-select v-model="form.data_type" class="w-full" placeholder="请选择数据类型">
              <el-option
                v-for="item in dataTypeOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="关联单位" prop="unit_id">
            <el-select
              v-model="form.unit_id"
              class="w-full"
              clearable
              filterable
              remote
              reserve-keyword
              placeholder="可选，适用于数值型属性"
              :remote-method="searchUnits"
              :loading="unitLoading"
            >
              <el-option
                v-for="unit in unitOptions"
                :key="unit.id"
                :label="`${unit.name} (${unit.symbol || unit.code})`"
                :value="unit.id"
              />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item label="适用资源" prop="applicable_resource_types">
        <el-checkbox-group v-model="form.applicable_resource_types">
          <el-checkbox
            v-for="item in resourceTypeOptions"
            :key="item.value"
            :value="item.value"
          >
            {{ item.label }}
          </el-checkbox>
        </el-checkbox-group>
      </el-form-item>

      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="默认值" prop="default_value">
            <el-input v-model="form.default_value" maxlength="255" placeholder="可选默认值" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="是否必填" prop="is_required">
            <el-switch v-model="form.is_required" active-text="必填" inactive-text="选填" />
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item v-if="form.data_type === 'ENUM'" label="枚举值" prop="enum_values_text">
        <el-input
          v-model="form.enum_values_text"
          type="textarea"
          :rows="3"
          placeholder="多个枚举值请使用英文逗号分隔，例如：LOW,MIDDLE,HIGH"
        />
      </el-form-item>

      <el-form-item label="描述" prop="description">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="3"
          maxlength="256"
          show-word-limit
          placeholder="请输入属性描述"
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
import { attrDefinitionApi, unitApi } from '@/api/masterData'
import { useDictionaryStore } from '@/stores/dictionaries'
import type {
  AttrDataType,
  AttrDefinition,
  AttrDefinitionCreate,
  AttrDefinitionUpdate,
  ResourceType,
  Unit,
} from '@/api/masterData'

interface AttrFormModel {
  name: string
  code: string
  data_type: AttrDataType | ''
  unit_id: number | null
  applicable_resource_types: ResourceType[]
  default_value: string
  enum_values_text: string
  is_required: boolean
  description: string
}

const props = defineProps<{
  modelValue: boolean
  data?: AttrDefinition | null
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
const unitLoading = ref(false)
const formRef = ref<FormInstance>()
const unitOptions = ref<Unit[]>([])
const dictionaryStore = useDictionaryStore()

const dataTypeOptions = computed<Array<{ label: string; value: AttrDataType }>>(() =>
  dictionaryStore.getOptions('ATTR_DATA_TYPE').map((item) => ({
    label: item.label,
    value: item.value as AttrDataType,
  })),
)

const resourceTypeOptions = computed<Array<{ label: string; value: ResourceType }>>(() =>
  dictionaryStore.getOptions('RESOURCE_TYPE').map((item) => ({
    label: item.label,
    value: item.value as ResourceType,
  })),
)

const form = reactive<AttrFormModel>({
  name: '',
  code: '',
  data_type: '',
  unit_id: null,
  applicable_resource_types: [],
  default_value: '',
  enum_values_text: '',
  is_required: false,
  description: '',
})

const rules: FormRules<AttrFormModel> = {
  name: [
    { required: true, message: '请输入属性名称', trigger: 'blur' },
    { min: 1, max: 50, message: '属性名称长度为 1-50 个字符', trigger: 'blur' },
  ],
  code: [
    { required: true, message: '请输入属性编码', trigger: 'blur' },
    { pattern: /^[a-zA-Z][a-zA-Z0-9_]*$/, message: '属性编码必须以英文开头，仅包含字母、数字和下划线', trigger: 'blur' },
  ],
  data_type: [{ required: true, message: '请选择数据类型', trigger: 'change' }],
  applicable_resource_types: [
    {
      type: 'array',
      required: true,
      min: 1,
      message: '请至少选择一个适用资源类型',
      trigger: 'change',
    },
  ],
  enum_values_text: [
    {
      validator: (_rule, value: string, callback) => {
        if (form.data_type !== 'ENUM') {
          callback()
          return
        }
        if (parseEnumValues(value).length === 0) {
          callback(new Error('枚举类型必须至少填写一个枚举值'))
          return
        }
        callback()
      },
      trigger: 'blur',
    },
  ],
}

watch(
  () => props.modelValue,
  async (opened: boolean) => {
    if (opened) {
      await dictionaryStore.ensureLoaded()
      hydrateForm()
      await searchUnits('')
    }
  },
)

function hydrateForm() {
  form.name = props.data?.name ?? ''
  form.code = props.data?.code ?? ''
  form.data_type = props.data?.data_type ?? ''
  form.unit_id = props.data?.unit_id ?? null
  form.applicable_resource_types = [...(props.data?.applicable_resource_types ?? [])]
  form.default_value = props.data?.default_value ?? ''
  form.enum_values_text = (props.data?.enum_values ?? []).join(',')
  form.is_required = props.data?.is_required ?? false
  form.description = props.data?.description ?? ''
}

function resetForm() {
  formRef.value?.clearValidate()
  form.name = ''
  form.code = ''
  form.data_type = ''
  form.unit_id = null
  form.applicable_resource_types = []
  form.default_value = ''
  form.enum_values_text = ''
  form.is_required = false
  form.description = ''
}

function normalizeText(value: string): string | null {
  const trimmed = value.trim()
  return trimmed.length > 0 ? trimmed : null
}

function parseEnumValues(text: string): string[] {
  return text
    .split(',')
    .map((item: string) => item.trim())
    .filter((item: string) => item.length > 0)
}

async function searchUnits(keyword: string) {
  unitLoading.value = true
  try {
    const response = await unitApi.list({ keyword: keyword || undefined, page: 1, size: 200 })
    unitOptions.value = response.data.items
  } catch {
    ElMessage.error('加载单位选项失败')
  } finally {
    unitLoading.value = false
  }
}

async function handleSubmit() {
  const validated = await formRef.value?.validate().then(() => true).catch(() => false)
  if (!validated || form.data_type === '') {
    return
  }

  submitting.value = true
  try {
    const enumValues = form.data_type === 'ENUM' ? parseEnumValues(form.enum_values_text) : null

    if (isEdit.value && props.data) {
      const payload: AttrDefinitionUpdate = {
        name: form.name.trim(),
        data_type: form.data_type,
        unit_id: form.unit_id,
        applicable_resource_types: [...form.applicable_resource_types],
        default_value: normalizeText(form.default_value),
        enum_values: enumValues,
        is_required: form.is_required,
        description: normalizeText(form.description),
      }
      await attrDefinitionApi.update(props.data.id, payload)
      ElMessage.success('柔性属性已更新')
    } else {
      const payload: AttrDefinitionCreate = {
        name: form.name.trim(),
        code: form.code.trim(),
        data_type: form.data_type,
        unit_id: form.unit_id,
        applicable_resource_types: [...form.applicable_resource_types],
        default_value: normalizeText(form.default_value),
        enum_values: enumValues,
        is_required: form.is_required,
        description: normalizeText(form.description),
      }
      await attrDefinitionApi.create(payload)
      ElMessage.success('柔性属性已创建')
    }

    visible.value = false
    emit('success')
  } catch {
    // 请求失败提示由全局拦截器统一处理
  } finally {
    submitting.value = false
  }
}
</script>