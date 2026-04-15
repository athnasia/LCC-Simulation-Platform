<template>
  <el-dialog
    v-model="visible"
    :title="isEdit ? '编辑权限' : '新建权限'"
    width="520px"
    :close-on-click-modal="false"
    @closed="resetForm"
  >
    <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
      <el-form-item label="权限名称" prop="name">
        <el-input v-model="form.name" placeholder="如：材料主数据读取" maxlength="64" />
      </el-form-item>
      <el-form-item label="权限编码" prop="code">
        <el-input
          v-model="form.code"
          placeholder="全大写，如 MATERIAL_READ"
          maxlength="100"
          :disabled="isEdit"
        />
      </el-form-item>
      <el-form-item label="资源路径" prop="resource">
        <el-input v-model="form.resource" placeholder="如 /system/users" maxlength="200" />
      </el-form-item>
      <el-form-item label="操作类型" prop="action">
        <el-select v-model="form.action" class="w-full">
          <el-option
            v-for="option in actionOptions"
            :key="option.value"
            :label="`${option.value} — ${option.label}`"
            :value="option.value"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="上级节点" prop="parent_id">
        <el-select v-model="form.parent_id" placeholder="不选则为顶级菜单/权限" clearable class="w-full">
          <el-option
            v-for="perm in parentOptions"
            :key="perm.id"
            :label="`${perm.name}（${perm.code}）`"
            :value="perm.id"
            :disabled="isEdit && perm.id === props.data?.id"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="描述" prop="description">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="2"
          maxlength="256"
          show-word-limit
          placeholder="选填"
        />
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
import { permApi } from '@/api/system'
import type { Permission, PermissionAction } from '@/api/system'
import { PERMISSION_ACTION_OPTIONS } from '@/constants/systemDictionaries'
import { useDictionaryStore } from '@/stores/dictionaries'

const props = defineProps<{
  modelValue: boolean
  data?: Permission | null
  parentOptions: Pick<Permission, 'id' | 'name' | 'code'>[]
  defaultParentId?: number | null
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
const dictionaryStore = useDictionaryStore()
const actionOptions = computed(
  () => dictionaryStore.getOptions('PERMISSION_ACTION', PERMISSION_ACTION_OPTIONS) as Array<{ label: string; value: PermissionAction }>,
)

const form = reactive({
  name: '',
  code: '',
  resource: '',
  action: 'read' as PermissionAction,
  description: null as string | null,
  parent_id: null as number | null,
})

const rules: FormRules = {
  name: [{ required: true, message: '请输入权限名称', trigger: 'blur' }],
  code: [
    { required: true, message: '请输入权限编码', trigger: 'blur' },
    { pattern: /^[A-Z0-9_]+$/, message: '只允许大写字母、数字和下划线', trigger: 'blur' },
  ],
  resource: [{ required: true, message: '请输入资源路径', trigger: 'blur' }],
  action: [{ required: true, message: '请选择操作类型', trigger: 'change' }],
}

watch(
  () => props.data,
  (perm) => {
    if (perm) {
      form.name = perm.name
      form.code = perm.code
      form.resource = perm.resource
      form.action = perm.action
      form.description = perm.description
      form.parent_id = perm.parent_id
      return
    }

    form.name = ''
    form.code = ''
    form.resource = ''
    form.action = 'read'
    form.description = null
    form.parent_id = props.defaultParentId ?? null
  },
  { immediate: true },
)

watch(
  () => props.defaultParentId,
  (defaultParentId) => {
    if (!props.data) {
      form.parent_id = defaultParentId ?? null
    }
  },
)

watch(
  () => props.modelValue,
  (val) => {
    if (val) {
      void dictionaryStore.ensureLoaded().catch(() => undefined)
    }
  },
)

async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    if (isEdit.value && props.data?.id) {
      await permApi.update(props.data.id, { ...form })
      ElMessage.success('更新成功')
    } else {
      await permApi.create({ ...form })
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
  form.description = null
  form.parent_id = props.defaultParentId ?? null
  form.action = 'read'
}
</script>
