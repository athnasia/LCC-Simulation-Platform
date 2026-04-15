<template>
  <el-dialog
    v-model="visible"
    :title="isEdit ? '编辑字典类型' : '新建字典类型'"
    width="560px"
    :close-on-click-modal="false"
    @closed="resetForm"
  >
    <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
      <el-form-item label="类型名称" prop="name">
        <el-input v-model="form.name" maxlength="64" placeholder="例如：属性数据类型" />
      </el-form-item>
      <el-form-item label="类型编码" prop="code">
        <el-input v-model="form.code" maxlength="64" placeholder="例如：ATTR_DATA_TYPE" :disabled="isEdit" />
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
import type { DictionaryType, DictionaryTypeCreate, DictionaryTypeUpdate } from '@/api/systemDictionary'

interface TypeFormModel {
  name: string
  code: string
  sort_order: number
  is_active: boolean
  description: string
}

const props = defineProps<{
  modelValue: boolean
  data?: DictionaryType | null
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
const form = reactive<TypeFormModel>({
  name: '',
  code: '',
  sort_order: 0,
  is_active: true,
  description: '',
})

const rules: FormRules<TypeFormModel> = {
  name: [{ required: true, message: '请输入类型名称', trigger: 'blur' }],
  code: [
    { required: true, message: '请输入类型编码', trigger: 'blur' },
    { pattern: /^[A-Z][A-Z0-9_]*$/, message: '类型编码必须为大写英文和下划线', trigger: 'blur' },
  ],
}

watch(
  () => props.modelValue,
  (opened: boolean) => {
    if (opened) {
      form.name = props.data?.name ?? ''
      form.code = props.data?.code ?? ''
      form.sort_order = props.data?.sort_order ?? 0
      form.is_active = props.data?.is_active ?? true
      form.description = props.data?.description ?? ''
    }
  },
)

function resetForm() {
  formRef.value?.clearValidate()
  form.name = ''
  form.code = ''
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
  if (!validated) {
    return
  }

  submitting.value = true
  try {
    if (props.data) {
      const payload: DictionaryTypeUpdate = {
        name: form.name.trim(),
        sort_order: form.sort_order,
        is_active: form.is_active,
        description: normalizeText(form.description),
      }
      await systemDictionaryApi.updateType(props.data.id, payload)
      ElMessage.success('字典类型已更新')
    } else {
      const payload: DictionaryTypeCreate = {
        name: form.name.trim(),
        code: form.code.trim(),
        sort_order: form.sort_order,
        is_active: form.is_active,
        description: normalizeText(form.description),
      }
      await systemDictionaryApi.createType(payload)
      ElMessage.success('字典类型已创建')
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