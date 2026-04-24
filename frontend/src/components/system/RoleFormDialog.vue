<template>
  <el-dialog
    v-model="visible"
    :title="isEdit ? '编辑角色' : '新建角色'"
    width="560px"
    :close-on-click-modal="false"
    @closed="resetForm"
  >
    <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="角色名称" prop="name">
            <el-input v-model="form.name" placeholder="如：工艺工程师" maxlength="64" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="角色编码" prop="code">
            <el-input
              v-model="form.code"
              placeholder="如 PROCESS_ENG"
              maxlength="64"
              :disabled="isEdit"
            />
          </el-form-item>
        </el-col>
      </el-row>

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

      <el-form-item label="状态" prop="is_active">
        <el-switch v-model="form.is_active" active-text="启用" inactive-text="禁用" />
      </el-form-item>

      <el-divider content-position="left">
        <span class="text-xs text-gray-400">绑定权限（{{ form.permission_ids.length }} 项已选）</span>
      </el-divider>

      <div class="perm-grid max-h-72 overflow-y-auto border border-gray-200 rounded-md p-3">
        <el-empty v-if="allPermissions.length === 0" description="暂无可选权限" :image-size="48" />
        <el-tree
          v-else
          ref="permissionTreeRef"
          :data="permissionTree"
          node-key="id"
          show-checkbox
          default-expand-all
          :check-strictly="true"
          :props="{ children: 'children', label: 'name' }"
          class="permission-tree"
          @check="syncCheckedPermissions"
        >
          <template #default="{ data }">
            <div class="flex items-center gap-2 min-w-0 py-0.5">
              <span class="text-sm truncate">{{ data.name }}</span>
              <el-tag size="small" class="!text-xs" :type="actionTagType(data.action)">
                {{ getActionLabel(data.action) }}
              </el-tag>
              <span class="text-xs text-gray-400 truncate">{{ data.code }}</span>
            </div>
          </template>
        </el-tree>
      </div>
    </el-form>

    <template #footer>
      <el-button @click="visible = false">取 消</el-button>
      <el-button type="primary" :loading="loading" @click="handleSubmit">确 定</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { roleApi } from '@/api/system'
import type { Permission, RoleDetail, PermissionAction } from '@/api/system'
import { PERMISSION_ACTION_OPTIONS } from '@/constants/systemDictionaries'
import { useDictionaryStore } from '@/stores/dictionaries'
import { resolveDictionaryLabel, resolveDictionarySortOrder, resolveDictionaryTagType } from '@/utils/dictionaryDisplay'

type PermissionTreeNode = Pick<Permission, 'id' | 'name' | 'code' | 'action' | 'resource' | 'parent_id'> & {
  children: PermissionTreeNode[]
}

const props = defineProps<{
  modelValue: boolean
  data?: RoleDetail | null
  allPermissions: Pick<Permission, 'id' | 'name' | 'code' | 'action' | 'resource' | 'parent_id'>[]
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
const permissionTreeRef = ref<any>()
const dictionaryStore = useDictionaryStore()
const permissionActionOptions = computed(() => dictionaryStore.getOptions('PERMISSION_ACTION', PERMISSION_ACTION_OPTIONS))

const form = reactive({
  name: '',
  code: '',
  description: null as string | null,
  is_active: true,
  permission_ids: [] as number[],
})

const rules: FormRules = {
  name: [{ required: true, message: '请输入角色名称', trigger: 'blur' }],
  code: [
    { required: true, message: '请输入角色编码', trigger: 'blur' },
    { pattern: /^[A-Z0-9_]+$/, message: '只允许大写字母、数字和下划线', trigger: 'blur' },
  ],
}

const permissionTree = computed<PermissionTreeNode[]>(() => buildPermissionTree(props.allPermissions))

const actionTagType = (action: PermissionAction) => {
  return resolveDictionaryTagType(permissionActionOptions.value, action)
}

const getActionLabel = (action: PermissionAction) => {
  return resolveDictionaryLabel(permissionActionOptions.value, action, action)
}

watch(
  () => props.data,
  (role) => {
    if (role) {
      form.name = role.name
      form.code = role.code
      form.description = role.description
      form.is_active = role.is_active
      form.permission_ids = role.permissions.map((p) => p.id)
      syncCheckedPermissionsLater()
      return
    }

    form.name = ''
    form.code = ''
    form.description = null
    form.is_active = true
    form.permission_ids = []
    syncCheckedPermissionsLater()
  },
  { immediate: true },
)

watch(
  () => props.modelValue,
  (visible) => {
    if (visible) {
      syncCheckedPermissionsLater()
    }
  },
)

watch(
  () => props.allPermissions,
  () => {
    syncCheckedPermissionsLater()
  },
  { deep: true },
)

async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    if (isEdit.value && props.data?.id) {
      await roleApi.update(props.data.id, { ...form })
      ElMessage.success('更新成功')
    } else {
      await roleApi.create({ ...form })
      ElMessage.success('创建成功')
    }
    emit('success')
    visible.value = false
  } finally {
    loading.value = false
  }
}

function syncCheckedPermissions() {
  form.permission_ids = (permissionTreeRef.value?.getCheckedKeys(false) ?? []) as number[]
}

function syncCheckedPermissionsLater() {
  nextTick(() => {
    permissionTreeRef.value?.setCheckedKeys(form.permission_ids)
  })
}

function buildPermissionTree(
  permissions: Pick<Permission, 'id' | 'name' | 'code' | 'action' | 'resource' | 'parent_id'>[],
): PermissionTreeNode[] {
  const nodes = permissions.map((permission) => ({ ...permission, children: [] as PermissionTreeNode[] }))
  const nodeMap = new Map(nodes.map((node) => [node.id, node]))
  const linkedNodeIds = new Set<number>()

  for (const node of nodes) {
    if (node.parent_id && nodeMap.has(node.parent_id)) {
      nodeMap.get(node.parent_id)!.children.push(node)
      linkedNodeIds.add(node.id)
    }
  }

  const rootCandidates = nodes.filter((node) => !linkedNodeIds.has(node.id))
  const groupedRoots = new Map<string, PermissionTreeNode[]>()
  for (const node of rootCandidates) {
    const key = node.children.length > 0 ? `node:${node.id}` : `resource:${node.resource}`
    if (!groupedRoots.has(key)) {
      groupedRoots.set(key, [])
    }
    groupedRoots.get(key)!.push(node)
  }

  const roots: PermissionTreeNode[] = []
  for (const group of groupedRoots.values()) {
    if (group.length === 1 || group.some((node) => node.children.length > 0)) {
      roots.push(...group)
      continue
    }

    const sortedGroup = [...group].sort((left, right) => {
      const actionDiff = resolveDictionarySortOrder(permissionActionOptions.value, left.action, 999)
        - resolveDictionarySortOrder(permissionActionOptions.value, right.action, 999)
      if (actionDiff !== 0) {
        return actionDiff
      }
      return left.name.localeCompare(right.name, 'zh-CN')
    })
    const root = sortedGroup.find((node) => node.action === 'read') ?? sortedGroup[0]
    root.children.push(...sortedGroup.filter((node) => node.id !== root.id))
    roots.push(root)
  }

  const sortTree = (items: PermissionTreeNode[]) => {
    items.sort((left, right) => {
      const actionDiff = resolveDictionarySortOrder(permissionActionOptions.value, left.action, 999)
        - resolveDictionarySortOrder(permissionActionOptions.value, right.action, 999)
      if (actionDiff !== 0) {
        return actionDiff
      }
      return left.name.localeCompare(right.name, 'zh-CN')
    })
    for (const item of items) {
      sortTree(item.children)
    }
  }

  sortTree(roots)
  return roots
}

function resetForm() {
  formRef.value?.resetFields()
  form.description = null
  form.is_active = true
  form.permission_ids = []
  permissionTreeRef.value?.setCheckedKeys([])
}
</script>

<style scoped>
.permission-tree :deep(.el-tree-node__content) {
  height: auto;
  min-height: 32px;
  align-items: center;
}
</style>
