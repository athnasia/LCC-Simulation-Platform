<template>
  <el-dialog
    v-model="visible"
    :title="isEdit ? '编辑用户' : '新建用户'"
    width="560px"
    :close-on-click-modal="false"
    @closed="resetForm"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="90px"
      size="default"
    >
      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="用户名" prop="username">
            <el-input
              v-model="form.username"
              placeholder="字母/数字/下划线"
              maxlength="64"
              :disabled="isEdit"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="真实姓名" prop="real_name">
            <el-input v-model="form.real_name" placeholder="请输入姓名" maxlength="64" />
          </el-form-item>
        </el-col>
      </el-row>

      <!-- 新建时才需要填写密码 -->
      <el-form-item v-if="!isEdit" label="初始密码" prop="password">
        <el-input
          v-model="form.password"
          type="password"
          placeholder="请输入初始密码"
          show-password
          maxlength="128"
        />
      </el-form-item>

      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="邮箱" prop="email">
            <el-input v-model="form.email" placeholder="选填" maxlength="128" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="手机号" prop="phone">
            <el-input v-model="form.phone" placeholder="选填" maxlength="11" />
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item label="所属部门" prop="department_id">
        <el-select
          v-model="form.department_id"
          placeholder="请选择部门（可选）"
          clearable
          class="w-full"
        >
          <el-option
            v-for="dept in deptOptions"
            :key="dept.id"
            :label="dept.name"
            :value="dept.id"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="绑定角色" prop="role_ids">
        <el-select
          v-model="form.role_ids"
          multiple
          collapse-tags
          collapse-tags-tooltip
          placeholder="请选择角色（可多选）"
          class="w-full"
        >
          <el-option
            v-for="role in roleOptions"
            :key="role.id"
            :label="role.name"
            :value="role.id"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="账号状态" prop="is_active">
        <el-switch v-model="form.is_active" active-text="启用" inactive-text="禁用" />
      </el-form-item>
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
import type { FormInstance, FormRules } from 'element-plus'
import { userApi } from '@/api/system'
import type { Department, RoleBase, UserDetail } from '@/api/system'

const props = defineProps<{
  modelValue: boolean
  data?: UserDetail | null
  deptOptions: Pick<Department, 'id' | 'name'>[]
  roleOptions: Pick<RoleBase, 'id' | 'name'>[]
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

const form = reactive({
  username: '',
  password: '',
  real_name: '',
  email: '' as string | null,
  phone: '' as string | null,
  department_id: null as number | null,
  role_ids: [] as number[],
  is_active: true,
})

const rules = computed<FormRules>(() => ({
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 64, message: '用户名长度 3-64', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_]+$/, message: '只允许字母、数字和下划线', trigger: 'blur' },
  ],
  password: isEdit.value
    ? []
    : [
        { required: true, message: '请输入初始密码', trigger: 'blur' },
      ],
  real_name: [{ required: true, message: '请输入真实姓名', trigger: 'blur' }],
  email: [{ type: 'email', message: '请输入有效邮箱地址', trigger: 'blur' }],
  phone: [{ pattern: /^1[3-9]\d{9}$/, message: '请输入有效的手机号', trigger: 'blur' }],
}))

watch(
  () => props.data,
  (user) => {
    if (user) {
      form.username = user.username
      form.real_name = user.real_name
      form.email = user.email
      form.phone = user.phone
      form.department_id = user.department_id
      form.role_ids = user.roles.map((r) => r.id)
      form.is_active = user.is_active
    }
  },
  { immediate: true },
)

async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    const payload = {
      username: form.username,
      real_name: form.real_name,
      email: form.email || null,
      phone: form.phone || null,
      department_id: form.department_id,
      role_ids: form.role_ids,
      is_active: form.is_active,
    }

    if (isEdit.value && props.data?.id) {
      await userApi.update(props.data.id, payload)
      ElMessage.success('更新成功')
    } else {
      await userApi.create({ ...payload, password: form.password })
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
  form.email = null
  form.phone = null
  form.department_id = null
  form.role_ids = []
  form.is_active = true
}
</script>
