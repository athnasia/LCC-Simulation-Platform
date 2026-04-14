<template>
  <el-dialog
    v-model="visible"
    :title="isEdit ? '编辑部门' : '新建部门'"
    width="480px"
    :close-on-click-modal="false"
    @closed="resetForm"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="80px"
      size="default"
    >
      <el-form-item label="部门名称" prop="name">
        <el-input v-model="form.name" placeholder="请输入部门名称" maxlength="100" />
      </el-form-item>
      <el-form-item label="部门编码" prop="code">
        <el-input
          v-model="form.code"
          placeholder="大写字母/数字/下划线，如 RD_CENTER"
          maxlength="50"
          :disabled="isEdit"
        />
      </el-form-item>
      <el-form-item label="上级部门" prop="parent_id">
        <el-select
          v-model="form.parent_id"
          placeholder="不选则为顶级部门"
          clearable
          class="w-full"
        >
          <el-option
            v-for="dept in parentOptions"
            :key="dept.id"
            :label="dept.name"
            :value="dept.id"
            :disabled="isEdit && dept.id === props.data?.id"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="排序" prop="sort_order">
        <el-input-number v-model="form.sort_order" :min="0" :max="9999" />
      </el-form-item>
      <el-form-item label="状态" prop="is_active">
        <el-switch v-model="form.is_active" active-text="启用" inactive-text="禁用" />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="visible = false">取 消</el-button>
      <el-button type="primary" :loading="loading" @click="handleSubmit">
        确 定
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { deptApi } from '@/api/system'
import type { Department } from '@/api/system'

// ── Props & Emits ──────────────────────────────────────────────
const props = defineProps<{
  modelValue: boolean
  data?: Department | null           // 传入则为编辑模式
  parentOptions: Department[]        // 可选上级部门列表（由父页面传入，避免重复请求）
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', val: boolean): void
  (e: 'success'): void
}>()

// ── 状态 ───────────────────────────────────────────────────────
const visible = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

const isEdit = computed(() => !!props.data?.id)
const loading = ref(false)
const formRef = ref<FormInstance>()

const form = reactive({
  name: '',
  code: '',
  parent_id: null as number | null,
  sort_order: 0,
  is_active: true,
})

const rules: FormRules = {
  name: [{ required: true, message: '请输入部门名称', trigger: 'blur' }],
  code: [
    { required: true, message: '请输入部门编码', trigger: 'blur' },
    { pattern: /^[A-Z0-9_-]+$/, message: '只允许大写字母、数字、下划线和短横线', trigger: 'blur' },
  ],
}

// ── 编辑时回填表单 ─────────────────────────────────────────────
watch(
  () => props.data,
  (dept) => {
    if (dept) {
      form.name = dept.name
      form.code = dept.code
      form.parent_id = dept.parent_id
      form.sort_order = dept.sort_order
      form.is_active = dept.is_active
    }
  },
  { immediate: true },
)

// ── 提交 ───────────────────────────────────────────────────────
async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    if (isEdit.value && props.data?.id) {
      await deptApi.update(props.data.id, {
        name: form.name,
        sort_order: form.sort_order,
        is_active: form.is_active,
        parent_id: form.parent_id,
      })
      ElMessage.success('更新成功')
    } else {
      await deptApi.create({ ...form })
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
  form.parent_id = null
  form.sort_order = 0
  form.is_active = true
}
</script>
