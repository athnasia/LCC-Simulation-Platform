<template>
  <el-dialog
    :model-value="modelValue"
    title="新建版本"
    width="500px"
    @update:model-value="emit('update:modelValue', $event)"
    @close="handleClose"
  >
    <el-form ref="formRef" :model="form" :rules="rules" label-width="120px">
      <el-form-item label="版本号" prop="version">
        <el-input-number v-model="form.version" :min="1" :max="999" style="width: 100%" />
      </el-form-item>
      
      <el-form-item label="复制自历史版本">
        <el-select
          v-model="form.clone_from_version_id"
          placeholder="留空则创建空白版本"
          clearable
          style="width: 100%"
        >
          <el-option
            v-for="v in existingVersions"
            :key="v.id"
            :label="`版本 ${v.version} (${getVersionStatusText(v.status)})`"
            :value="v.id"
          />
        </el-select>
        <el-text size="small" type="info">
          选择历史版本将完整复制其 BOM 结构、工艺路线和工序步骤
        </el-text>
      </el-form-item>
      
      <el-form-item label="描述" prop="description">
        <el-input v-model="form.description" type="textarea" :rows="3" placeholder="请输入版本描述" />
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
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { designSchemeVersionApi, type DesignSchemeVersion } from '@/api/engineering'

const props = defineProps<{
  modelValue: boolean
  schemeId: number | null
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  success: []
}>()

const formRef = ref<FormInstance>()
const loading = ref(false)
const existingVersions = ref<DesignSchemeVersion[]>([])

const form = reactive({
  scheme_id: 0,
  version: 1,
  clone_from_version_id: null as number | null,
  description: '',
})

const rules: FormRules = {
  version: [{ required: true, message: '请输入版本号', trigger: 'blur' }],
}

watch(() => props.modelValue, async (val) => {
  if (val && props.schemeId) {
    form.scheme_id = props.schemeId
    form.version = 1
    form.clone_from_version_id = null
    form.description = ''
    
    await loadExistingVersions()
  }
})

async function loadExistingVersions() {
  if (!props.schemeId) return
  
  try {
    const res = await designSchemeVersionApi.list({ scheme_id: props.schemeId, size: 100 })
    existingVersions.value = res.data.items || []
    
    if (existingVersions.value.length > 0) {
      const maxVersion = Math.max(...existingVersions.value.map(v => v.version))
      form.version = maxVersion + 1
    }
  } catch (error) {
    console.error('Failed to load existing versions:', error)
  }
}

function getVersionStatusText(status: string) {
  const map: Record<string, string> = {
    DRAFT: '草稿',
    RELEASED: '已发布',
    ARCHIVED: '已归档',
  }
  return map[status] || status
}

function handleClose() {
  formRef.value?.resetFields()
}

async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  
  loading.value = true
  try {
    await designSchemeVersionApi.create({
      scheme_id: form.scheme_id,
      version: form.version,
      clone_from_version_id: form.clone_from_version_id,
      description: form.description || null,
    })
    ElMessage.success('创建成功')
    emit('success')
    emit('update:modelValue', false)
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || '操作失败')
  } finally {
    loading.value = false
  }
}
</script>
