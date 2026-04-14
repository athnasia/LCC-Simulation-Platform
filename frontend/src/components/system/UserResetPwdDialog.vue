<template>
  <el-dialog
    v-model="visible"
    title="重置用户密码"
    width="400px"
    :close-on-click-modal="false"
    @closed="resetForm"
  >
    <el-alert
      type="warning"
      show-icon
      :closable="false"
      class="mb-4"
    >
      <template #title>
        即将重置用户 <strong>{{ props.username }}</strong> 的登录密码，操作将被记录至审计日志。
      </template>
    </el-alert>

    <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
      <el-form-item label="新密码" prop="new_password">
        <el-input
          v-model="form.new_password"
          type="password"
          show-password
          placeholder="请输入新密码"
          maxlength="128"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="visible = false">取 消</el-button>
      <el-button type="danger" :loading="loading" @click="handleSubmit">确认重置</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { userApi } from '@/api/system'

const props = defineProps<{
  modelValue: boolean
  userId: number
  username: string
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', val: boolean): void
  (e: 'success'): void
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

const loading = ref(false)
const formRef = ref<FormInstance>()
const form = reactive({ new_password: '' })

const rules: FormRules = {
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
  ],
}

async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await userApi.resetPassword(props.userId, { new_password: form.new_password })
    ElMessage.success('密码重置成功')
    emit('success')
    visible.value = false
  } finally {
    loading.value = false
  }
}

function resetForm() {
  formRef.value?.resetFields()
}
</script>
