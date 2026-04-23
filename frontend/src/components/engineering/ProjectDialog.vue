<template>
  <el-dialog
    :model-value="modelValue"
    :title="project ? '编辑项目' : '新建项目'"
    width="500px"
    @update:model-value="emit('update:modelValue', $event)"
    @close="handleClose"
  >
    <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
      <el-form-item label="项目名称" prop="name">
        <el-input v-model="form.name" placeholder="请输入项目名称" />
      </el-form-item>
      <el-form-item label="项目编码" prop="code">
        <el-input v-model="form.code" placeholder="请输入项目编码" :disabled="!!project" />
      </el-form-item>
      <el-form-item label="状态" prop="is_active">
        <el-switch v-model="form.is_active" active-text="启用" inactive-text="停用" />
      </el-form-item>
      <el-form-item label="描述" prop="description">
        <el-input v-model="form.description" type="textarea" :rows="3" placeholder="请输入项目描述" />
      </el-form-item>
    </el-form>
    
    <template #footer>
      <el-button @click="emit('update:modelValue', false)">取消</el-button>
      <el-button type="primary" :loading="loading" @click="handleSubmit">确定</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { ElMessage, FormInstance, FormRules } from 'element-plus'
import { projectApi } from '@/api/engineering'

const props = defineProps<{
  modelValue: boolean
  project: any | null
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  success: []
}>()

const formRef = ref<FormInstance>()
const loading = ref(false)

const form = reactive({
  name: '',
  code: '',
  is_active: true,
  description: '',
})

const rules: FormRules = {
  name: [{ required: true, message: '请输入项目名称', trigger: 'blur' }],
  code: [
    { required: true, message: '请输入项目编码', trigger: 'blur' },
    { pattern: /^[A-Z0-9_]+$/, message: '编码只能包含大写字母、数字和下划线', trigger: 'blur' },
  ],
}

watch(() => props.modelValue, (val) => {
  if (val) {
    if (props.project) {
      form.name = props.project.name || ''
      form.code = props.project.code || ''
      form.is_active = props.project.is_active ?? true
      form.description = props.project.description || ''
    } else {
      resetForm()
    }
  }
})

function resetForm() {
  form.name = ''
  form.code = ''
  form.is_active = true
  form.description = ''
}

function handleClose() {
  formRef.value?.resetFields()
}

async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  
  loading.value = true
  try {
    if (props.project) {
      await projectApi.update(props.project.id, form)
      ElMessage.success('更新成功')
    } else {
      await projectApi.create(form)
      ElMessage.success('创建成功')
    }
    emit('success')
    emit('update:modelValue', false)
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || '操作失败')
  } finally {
    loading.value = false
  }
}
</script>
