<template>
  <el-dialog
    :model-value="modelValue"
    :title="product ? '编辑产品' : '新建产品'"
    width="500px"
    @update:model-value="emit('update:modelValue', $event)"
    @close="handleClose"
  >
    <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
      <el-form-item label="产品名称" prop="name">
        <el-input v-model="form.name" placeholder="请输入产品名称" />
      </el-form-item>
      <el-form-item label="产品编码" prop="code">
        <el-input v-model="form.code" placeholder="请输入产品编码" :disabled="!!product" />
      </el-form-item>
      <el-form-item label="状态" prop="is_active">
        <el-switch v-model="form.is_active" active-text="启用" inactive-text="停用" />
      </el-form-item>
      <el-form-item label="描述" prop="description">
        <el-input v-model="form.description" type="textarea" :rows="3" placeholder="请输入产品描述" />
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
import { productApi } from '@/api/engineering'

const props = defineProps<{
  modelValue: boolean
  product: any | null
  projectId: number | null
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
  project_id: 0,
  is_active: true,
  description: '',
})

const rules: FormRules = {
  name: [{ required: true, message: '请输入产品名称', trigger: 'blur' }],
  code: [
    { required: true, message: '请输入产品编码', trigger: 'blur' },
    { pattern: /^[A-Z0-9_]+$/, message: '编码只能包含大写字母、数字和下划线', trigger: 'blur' },
  ],
}

watch(() => props.modelValue, (val) => {
  if (val) {
    if (props.product) {
      form.name = props.product.name || ''
      form.code = props.product.code || ''
      form.project_id = props.product.project_id || 0
      form.is_active = props.product.is_active ?? true
      form.description = props.product.description || ''
    } else {
      form.project_id = props.projectId || 0
      form.name = ''
      form.code = ''
      form.is_active = true
      form.description = ''
    }
  }
})

function handleClose() {
  formRef.value?.resetFields()
}

async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  
  loading.value = true
  try {
    if (props.product) {
      await productApi.update(props.product.id, form)
      ElMessage.success('更新成功')
    } else {
      await productApi.create(form)
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
