<template>
  <div class="flex gap-4 h-full">
    <el-card class="w-[420px] flex-shrink-0" shadow="never" body-style="padding:12px">
      <template #header>
        <div class="flex items-center justify-between gap-2">
          <span class="text-sm font-medium">菜单权限树</span>
          <el-button v-if="canWritePermissions" type="primary" link :icon="Plus" @click="openDialog()">
            新建根节点
          </el-button>
        </div>
      </template>

      <el-scrollbar max-height="calc(100vh - 220px)">
        <el-tree
          v-if="permissionTree.length > 0"
          :data="permissionTree"
          node-key="id"
          default-expand-all
          highlight-current
          :expand-on-click-node="false"
          :current-node-key="selectedPermission?.id"
          :props="{ children: 'children', label: 'name' }"
          class="permission-tree"
          @node-click="selectPermission"
        >
          <template #default="{ data }">
            <div class="flex items-center justify-between w-full gap-2 pr-1 py-0.5">
              <div class="min-w-0 flex-1">
                <div class="flex items-center gap-2 min-w-0">
                  <span class="text-sm truncate">{{ data.name }}</span>
                  <el-tag size="small" class="!text-xs" :type="actionTagType(data.action)">
                    {{ getActionLabel(data.action) }}
                  </el-tag>
                </div>
                <div class="text-xs text-gray-400 truncate mt-0.5">{{ data.resource }} · {{ data.code }}</div>
              </div>
              <div class="flex-shrink-0 flex items-center gap-1 permission-ops">
                <el-button
                  v-if="canWritePermissions"
                  link
                  size="small"
                  :icon="Plus"
                  @click.stop="openDialog(undefined, data.id)"
                />
                <el-button
                  v-if="canWritePermissions"
                  link
                  size="small"
                  :icon="Edit"
                  @click.stop="openDialog(data)"
                />
                <el-button
                  v-if="canDeletePermissions"
                  link
                  size="small"
                  :icon="Delete"
                  type="danger"
                  @click.stop="deletePermission(data)"
                />
              </div>
            </div>
          </template>
        </el-tree>
        <el-empty v-else description="暂无菜单权限" :image-size="52" />
      </el-scrollbar>
    </el-card>

    <el-card class="flex-1" shadow="never">
      <template #header>
        <div class="flex items-center justify-between gap-2">
          <span class="text-sm font-medium">节点详情</span>
          <el-button v-if="selectedPermission && canWritePermissions" link type="primary" @click="openDialog(selectedPermission)">
            编辑当前节点
          </el-button>
        </div>
      </template>

      <el-empty v-if="!selectedPermission" description="请选择左侧节点查看详情" :image-size="64" />
      <div v-else class="grid grid-cols-2 gap-4 text-sm">
        <div>
          <div class="text-xs text-gray-400 mb-1">名称</div>
          <div class="font-medium text-gray-800">{{ selectedPermission.name }}</div>
        </div>
        <div>
          <div class="text-xs text-gray-400 mb-1">编码</div>
          <div class="font-medium text-gray-800">{{ selectedPermission.code }}</div>
        </div>
        <div>
          <div class="text-xs text-gray-400 mb-1">资源路径</div>
          <div class="font-medium text-gray-800 break-all">{{ selectedPermission.resource }}</div>
        </div>
        <div>
          <div class="text-xs text-gray-400 mb-1">操作类型</div>
          <el-tag :type="actionTagType(selectedPermission.action)">{{ getActionLabel(selectedPermission.action) }}</el-tag>
        </div>
        <div class="col-span-2">
          <div class="text-xs text-gray-400 mb-1">描述</div>
          <div class="text-gray-700 leading-6">{{ selectedPermission.description || '—' }}</div>
        </div>
        <div>
          <div class="text-xs text-gray-400 mb-1">父节点</div>
          <div class="text-gray-700">{{ parentNameMap[selectedPermission.parent_id ?? 0] || '顶级节点' }}</div>
        </div>
        <div>
          <div class="text-xs text-gray-400 mb-1">子节点数</div>
          <div class="text-gray-700">{{ childCountMap[selectedPermission.id] ?? 0 }}</div>
        </div>
      </div>
    </el-card>

    <PermissionFormDialog
      v-model="dialogVisible"
      :data="currentPermission"
      :default-parent-id="dialogParentId"
      :parent-options="permissionList"
      @success="loadPermissions"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete, Edit, Plus } from '@element-plus/icons-vue'
import { permApi } from '@/api/system'
import type { Permission, PermissionAction } from '@/api/system'
import PermissionFormDialog from '@/components/system/PermissionFormDialog.vue'
import { PERMISSION_ACTION_OPTIONS } from '@/constants/systemDictionaries'
import { useAuthStore } from '@/stores/auth'
import { useDictionaryStore } from '@/stores/dictionaries'
import { resolveDictionaryLabel, resolveDictionarySortOrder, resolveDictionaryTagType } from '@/utils/dictionaryDisplay'

type PermissionTreeNode = Permission & { children: PermissionTreeNode[] }

const authStore = useAuthStore()
const dictionaryStore = useDictionaryStore()
const canWritePermissions = computed(() => authStore.hasPermissionScope('/system/permissions:write'))
const canDeletePermissions = computed(() => authStore.hasPermissionScope('/system/permissions:delete'))
const permissionActionOptions = computed(() => dictionaryStore.getOptions('PERMISSION_ACTION', PERMISSION_ACTION_OPTIONS))

const permissionList = ref<Permission[]>([])
const selectedPermission = ref<Permission | null>(null)
const currentPermission = ref<Permission | null>(null)
const dialogVisible = ref(false)
const dialogParentId = ref<number | null>(null)

const permissionTree = computed<PermissionTreeNode[]>(() => buildPermissionTree(permissionList.value))
const parentNameMap = computed<Record<number, string>>(() => Object.fromEntries(permissionList.value.map((item) => [item.id, item.name])))
const childCountMap = computed<Record<number, number>>(() => {
  const counts: Record<number, number> = {}
  for (const permission of permissionList.value) {
    if (permission.parent_id) {
      counts[permission.parent_id] = (counts[permission.parent_id] ?? 0) + 1
    }
  }
  return counts
})

async function loadPermissions() {
  const res = await permApi.list({ size: 500 })
  permissionList.value = res.data.items

  if (!selectedPermission.value) {
    selectedPermission.value = permissionList.value[0] ?? null
    return
  }

  selectedPermission.value = permissionList.value.find((item) => item.id === selectedPermission.value?.id) ?? permissionList.value[0] ?? null
}

function selectPermission(permission: Permission) {
  selectedPermission.value = permission
}

function openDialog(permission?: Permission, parentId: number | null = null) {
  currentPermission.value = permission ?? null
  dialogParentId.value = permission ? permission.parent_id : parentId
  dialogVisible.value = true
}

async function deletePermission(permission: Permission) {
  await ElMessageBox.confirm(`确定删除节点「${permission.name}」吗？`, '警告', { type: 'warning' })
  await permApi.remove(permission.id)
  ElMessage.success('已删除')
  if (selectedPermission.value?.id === permission.id) {
    selectedPermission.value = null
  }
  await loadPermissions()
}

function actionTagType(action: PermissionAction) {
  return resolveDictionaryTagType(permissionActionOptions.value, action, '')
}

function getActionLabel(action: PermissionAction) {
  return resolveDictionaryLabel(permissionActionOptions.value, action, action)
}

function buildPermissionTree(items: Permission[]): PermissionTreeNode[] {
  const nodes = items.map((item) => ({ ...item, children: [] as PermissionTreeNode[] }))
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
    const groupKey = node.children.length > 0 ? `node:${node.id}` : `resource:${node.resource}`
    if (!groupedRoots.has(groupKey)) {
      groupedRoots.set(groupKey, [])
    }
    groupedRoots.get(groupKey)!.push(node)
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

  const sortTree = (treeNodes: PermissionTreeNode[]) => {
    treeNodes.sort((left, right) => {
      const actionDiff = resolveDictionarySortOrder(permissionActionOptions.value, left.action, 999)
        - resolveDictionarySortOrder(permissionActionOptions.value, right.action, 999)
      if (actionDiff !== 0) {
        return actionDiff
      }
      return left.name.localeCompare(right.name, 'zh-CN')
    })
    for (const node of treeNodes) {
      sortTree(node.children)
    }
  }

  sortTree(roots)
  return roots
}

onMounted(loadPermissions)
</script>

<style scoped>
.permission-tree :deep(.el-tree-node__content) {
  height: auto;
  min-height: 42px;
  border-radius: 8px;
}

.permission-tree :deep(.el-tree-node__content:hover) {
  background-color: #f9fafb;
}

.permission-tree :deep(.el-tree-node__content:hover .permission-ops) {
  opacity: 1;
}

.permission-tree :deep(.el-tree--highlight-current .el-tree-node.is-current > .el-tree-node__content) {
  background-color: #eef2ff;
  color: #4338ca;
}

.permission-ops {
  opacity: 0;
}
</style>