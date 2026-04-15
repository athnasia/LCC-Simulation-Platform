<template>
  <el-dialog
    v-model="visible"
    :title="isEdit ? '编辑字典项' : '新建字典项'"
    width="620px"
    :close-on-click-modal="false"
    @closed="resetForm"
  >
    <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
      <el-form-item label="所属类型" prop="dict_type_id">
        <el-select v-model="form.dict_type_id" class="w-full" placeholder="请选择字典类型" :disabled="isEdit || typeLocked">
          <el-option v-for="type in typeOptions" :key="type.id" :label="`${type.name} (${type.code})`" :value="type.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="存储值" prop="value">
        <el-input v-model="form.value" maxlength="100" placeholder="例如：STRING / MATERIAL / BASE" :disabled="isEdit" />
      </el-form-item>
      <el-form-item label="显示标签" prop="label">
        <el-input v-model="form.label" maxlength="100" placeholder="例如：字符串 / 材料 / 基准单位" />
      </el-form-item>
      <el-form-item label="排序值" prop="sort_order">
        <el-input-number v-model="form.sort_order" :min="0" class="w-full" />
      </el-form-item>
      <el-form-item label="启用状态" prop="is_active">
        <el-switch v-model="form.is_active" active-text="启用" inactive-text="禁用" />
      </el-form-item>
      <el-form-item label="描述" prop="description">
        <el-input v-model="form.description" type="textarea" :rows="3" maxlength="256" show-word-limit />
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
import { systemDictionaryApi } from '@/api/systemDictionary'
import type {
  DictionaryItem,
  DictionaryItemCreate,
  DictionaryItemUpdate,
  DictionaryType,
} from '@/api/systemDictionary'

interface ItemFormModel {
  dict_type_id: number | null
  value: string
  label: string
  sort_order: number
  is_active: boolean
  description: string
}

const props = defineProps<{
  modelValue: boolean
  data?: DictionaryItem | null
  typeOptions: DictionaryType[]
  defaultTypeId?: number | null
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
const typeLocked = computed(() => Boolean(props.defaultTypeId))
const submitting = ref(false)
const formRef = ref<FormInstance>()
const form = reactive<ItemFormModel>({
  dict_type_id: null,
  value: '',
  label: '',
  sort_order: 0,
  is_active: true,
  description: '',
})

const rules: FormRules<ItemFormModel> = {
  dict_type_id: [{ required: true, message: '请选择字典类型', trigger: 'change' }],
  value: [{ required: true, message: '请输入存储值', trigger: 'blur' }],
  label: [{ required: true, message: '请输入显示标签', trigger: 'blur' }],
}

watch(
  () => props.modelValue,
  (opened: boolean) => {
    if (opened) {
      form.dict_type_id = props.data?.dict_type_id ?? props.defaultTypeId ?? null
      form.value = props.data?.value ?? ''
      form.label = props.data?.label ?? ''
      form.sort_order = props.data?.sort_order ?? 0
      form.is_active = props.data?.is_active ?? true
      form.description = props.data?.description ?? ''
    }
  },
)

function resetForm() {
  formRef.value?.clearValidate()
  form.dict_type_id = null
  form.value = ''
  form.label = ''
  form.sort_order = 0
  form.is_active = true
  form.description = ''
}

function normalizeText(value: string): string | null {
  const trimmed = value.trim()
  return trimmed.length > 0 ? trimmed : null
}

async function handleSubmit() {
  const validated = await formRef.value?.validate().then(() => true).catch(() => false)
  if (!validated || form.dict_type_id === null) {
    return
  }

  submitting.value = true
  try {
    if (props.data) {
      const payload: DictionaryItemUpdate = {
        label: form.label.trim(),
        sort_order: form.sort_order,
        is_active: form.is_active,
        description: normalizeText(form.description),
      }
      await systemDictionaryApi.updateItem(props.data.id, payload)
      ElMessage.success('字典项已更新')
    } else {
      const payload: DictionaryItemCreate = {
        dict_type_id: form.dict_type_id,
        value: form.value.trim(),
        label: form.label.trim(),
        sort_order: form.sort_order,
        is_active: form.is_active,
        description: normalizeText(form.description),
      }
      await systemDictionaryApi.createItem(payload)
      ElMessage.success('字典项已创建')
    }
    visible.value = false
    emit('success')
  } catch {
    // 统一错误提示由请求拦截器处理
  } finally {
    submitting.value = false
  }
}
</script>