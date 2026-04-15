<template>
  <el-dialog
    v-model="visible"
    :title="isEdit ? '编辑量纲' : '新建量纲'"
    width="560px"
    :close-on-click-modal="false"
    @closed="resetForm"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="92px"
    >
      <el-form-item label="量纲名称" prop="name">
        <el-input v-model="form.name" maxlength="50" placeholder="例如：长度、质量、时间" />
      </el-form-item>
      <el-form-item label="量纲编码" prop="code">
        <el-input
          v-model="form.code"
          maxlength="30"
          placeholder="例如：LENGTH"
          :disabled="isEdit"
        />
      </el-form-item>
      <el-form-item label="排序值" prop="sort_order">
        <el-input-number v-model="form.sort_order" :min="0" :step="10" class="w-full" />
      </el-form-item>
      <el-form-item label="描述" prop="description">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="3"
          maxlength="256"
          show-word-limit
          placeholder="请输入量纲描述"
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
import { unitDimensionApi } from '@/api/masterData'
import type { UnitDimension, UnitDimensionCreate, UnitDimensionUpdate } from '@/api/masterData'

interface DimensionFormModel {
  name: string
  code: string
  sort_order: number
  description: string
}

const props = defineProps<{
  modelValue: boolean
  data?: UnitDimension | null
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
const form = reactive<DimensionFormModel>({
  name: '',
  code: '',
  sort_order: 0,
  description: '',
})

const rules: FormRules<DimensionFormModel> = {
  name: [
    { required: true, message: '请输入量纲名称', trigger: 'blur' },
    { min: 1, max: 50, message: '量纲名称长度为 1-50 个字符', trigger: 'blur' },
  ],
  code: [
    { required: true, message: '请输入量纲编码', trigger: 'blur' },
    { pattern: /^[A-Z][A-Z0-9_]*$/, message: '量纲编码必须为纯大写英文或下划线', trigger: 'blur' },
  ],
}

watch(
  () => props.modelValue,
  (opened: boolean) => {
    if (opened) {
      hydrateForm()
    }
  },
)

function hydrateForm() {
  form.name = props.data?.name ?? ''
  form.code = props.data?.code ?? ''
  form.sort_order = props.data?.sort_order ?? 0
  form.description = props.data?.description ?? ''
}

function resetForm() {
  formRef.value?.clearValidate()
  form.name = ''
  form.code = ''
  form.sort_order = 0
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
    if (isEdit.value && props.data) {
      const payload: UnitDimensionUpdate = {
        name: form.name.trim(),
        sort_order: form.sort_order,
        description: normalizeText(form.description),
      }
      await unitDimensionApi.update(props.data.id, payload)
      ElMessage.success('量纲已更新')
    } else {
      const payload: UnitDimensionCreate = {
        name: form.name.trim(),
        code: form.code.trim(),
        sort_order: form.sort_order,
        description: normalizeText(form.description),
      }
      await unitDimensionApi.create(payload)
      ElMessage.success('量纲已创建')
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