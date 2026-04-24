<template>
  <div class="flex h-full gap-4">
    <el-card class="w-[420px] flex-shrink-0" shadow="never" body-style="padding: 16px;">
      <template #header>
        <div class="flex items-center justify-between gap-2">
          <span class="text-sm font-semibold text-slate-800">菜单权限树</span>
          <el-button v-if="canWritePermissions" type="primary" link :icon="Plus" @click="openDialog()">
            新建根节点
          </el-button>
        </div>
      </template>

      <div class="mb-3">
        <el-input
          v-model="filterText"
          clearable
          :prefix-icon="Search"
          placeholder="搜索节点名称..."
        />
      </div>

      <div class="h-[calc(100vh-200px)] overflow-y-auto pr-1">
        <el-tree
          v-if="permissionTree.length > 0"
          ref="treeRef"
          :data="permissionTree"
          node-key="id"
          default-expand-all
          highlight-current
          :expand-on-click-node="false"
          :current-node-key="selectedPermission?.id"
          :filter-node-method="filterNode"
          :props="{ children: 'children', label: 'name' }"
          class="rounded-xl bg-slate-50/70 p-2"
          @node-click="selectPermission"
        >
          <template #default="{ node, data }">
            <div class="group flex w-full items-center gap-2 rounded-lg px-2 py-1.5">
              <div class="flex min-w-0 flex-1 items-center gap-2">
                <el-icon class="flex-shrink-0 text-slate-500">
                  <component :is="getNodeIcon(data)" />
                </el-icon>
                <span
                  class="truncate text-sm"
                  :class="node.isCurrent ? 'font-semibold text-indigo-700' : 'font-medium text-slate-700'"
                >
                  {{ data.name }}
                </span>
              </div>

              <el-tag size="small" class="!ml-auto !mr-1 !text-xs" :type="actionTagType(data.action)">
                {{ getActionLabel(data.action) }}
              </el-tag>

              <div class="flex flex-shrink-0 items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100">
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
      </div>
    </el-card>

    <el-card class="flex-1" shadow="never" body-style="padding: 20px;">
      <template #header>
        <div class="flex items-center justify-between gap-3">
          <span class="text-base font-semibold text-slate-900">节点详情</span>
          <el-button
            v-if="canWritePermissions"
            type="primary"
            :icon="Edit"
            :disabled="!selectedPermission"
            @click="openDialog(selectedPermission ?? undefined)"
          >
            编辑节点
          </el-button>
        </div>
      </template>

      <el-empty v-if="!selectedPermission" description="请选择左侧节点查看详情" :image-size="64" />

      <div v-else class="space-y-5">
        <section class="space-y-3">
          <div class="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">基础信息</div>
          <el-descriptions border :column="2" size="large">
            <el-descriptions-item label="名称">
              <span class="font-medium text-slate-800">{{ selectedPermission.name }}</span>
            </el-descriptions-item>
            <el-descriptions-item label="编码">
              <span class="font-medium text-slate-700">{{ selectedPermission.code }}</span>
            </el-descriptions-item>
            <el-descriptions-item label="节点类型">
              <span class="text-slate-700">{{ getNodeKind(selectedPermission) }}</span>
            </el-descriptions-item>
            <el-descriptions-item label="操作类型">
              <el-tag size="small" :type="actionTagType(selectedPermission.action)">
                {{ getActionLabel(selectedPermission.action) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="父节点名称" :span="2">
              <span class="text-slate-700">{{ parentNameMap[selectedPermission.parent_id ?? 0] || '顶级节点' }}</span>
            </el-descriptions-item>
          </el-descriptions>
        </section>

        <section class="space-y-3">
          <div class="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">技术路由</div>
          <el-descriptions border :column="2" size="large">
            <el-descriptions-item label="前端路由">
              <span class="break-all text-slate-700">{{ getRouteText(selectedPermission) }}</span>
            </el-descriptions-item>
            <el-descriptions-item label="资源路径">
              <span class="break-all text-slate-700">{{ selectedPermission.resource }}</span>
            </el-descriptions-item>
            <el-descriptions-item label="数据表" :span="2">
              <span class="break-all text-slate-700">{{ getTableText(selectedPermission) }}</span>
            </el-descriptions-item>
          </el-descriptions>
        </section>

        <section class="space-y-3">
          <div class="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">备注说明</div>
          <el-descriptions border :column="2" size="large">
            <el-descriptions-item label="描述信息" :span="2">
              <div class="leading-7 text-slate-700">{{ selectedPermission.description || '—' }}</div>
            </el-descriptions-item>
          </el-descriptions>
        </section>
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
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { TreeInstance } from 'element-plus'
import { Coin, Delete, Document, Edit, Folder, Plus, Pointer, Search } from '@element-plus/icons-vue'
import { permApi } from '@/api/system'
import type { Permission, PermissionAction } from '@/api/system'
import PermissionFormDialog from '@/components/system/PermissionFormDialog.vue'
import { PERMISSION_ACTION_OPTIONS } from '@/constants/systemDictionaries'
import { useAuthStore } from '@/stores/auth'
import { useDictionaryStore } from '@/stores/dictionaries'
import { resolveDictionaryLabel, resolveDictionarySortOrder, resolveDictionaryTagType } from '@/utils/dictionaryDisplay'

type PermissionNodeType = 'menu' | 'page' | 'action' | 'resource'
type PermissionTreeNode = Permission & { children: PermissionTreeNode[]; node_type: PermissionNodeType }
type PermissionMeta = {
  routes?: string[]
  tables?: string[]
  kind?: string
  order?: number
}

const PERMISSION_META_BY_RESOURCE: Record<string, PermissionMeta> = {
  '/dashboard': { routes: ['/dashboard'], tables: ['驾驶舱聚合视图'], kind: '一级菜单', order: 10 },
  '/master-data': { kind: '一级菜单', order: 20 },
  '/master-data/dictionaries': {
    routes: ['/master-data/dictionaries'],
    tables: ['md_attr_definition', 'md_resource_category', 'md_unit_dimension', 'md_unit', 'md_unit_conversion'],
    kind: '页面',
    order: 21,
  },
  '/master-data/dict-templates': {
    routes: ['/master-data/dictionaries'],
    tables: ['md_attr_definition', 'md_resource_category', 'md_unit_dimension', 'md_unit', 'md_unit_conversion'],
    kind: '数据资源',
    order: 211,
  },
  '/master-data/materials': { routes: ['/master-data/materials'], tables: ['md_material'], kind: '页面/数据资源', order: 22 },
  '/master-data/equipments': { routes: ['/master-data/equipments'], tables: ['md_equipment'], kind: '页面/数据资源', order: 23 },
  '/master-data/processes': { routes: ['/master-data/processes'], tables: ['md_process', 'md_process_resource'], kind: '页面/数据资源', order: 24 },
  '/master-data/labor': { routes: ['/master-data/labor'], tables: ['md_labor'], kind: '页面/数据资源', order: 25 },
  '/master-data/energy': { routes: ['/master-data/energy'], tables: ['md_energy_rate', 'md_energy_calendar'], kind: '页面/数据资源', order: 26 },
  '/engineering': { kind: '一级菜单', order: 30 },
  '/engineering/projects': {
    routes: ['/engineering/projects'],
    tables: ['eng_project', 'eng_product', 'eng_design_scheme', 'eng_design_scheme_version'],
    kind: '页面',
    order: 31,
  },
  '/engineering/products': { routes: ['/engineering/projects'], tables: ['eng_product'], kind: '数据资源', order: 311 },
  '/engineering/schemes': { routes: ['/engineering/projects'], tables: ['eng_design_scheme'], kind: '数据资源', order: 312 },
  '/engineering/scheme-versions': { routes: ['/engineering/projects'], tables: ['eng_design_scheme_version'], kind: '数据资源', order: 313 },
  '/engineering/workbench': {
    routes: ['/engineering/workbench'],
    tables: ['eng_bom_node', 'eng_component_process_route', 'eng_route_step_bind'],
    kind: '页面',
    order: 32,
  },
  '/engineering/bom-nodes': { routes: ['/engineering/workbench'], tables: ['eng_bom_node'], kind: '数据资源', order: 321 },
  '/engineering/process-routes': { routes: ['/engineering/workbench'], tables: ['eng_component_process_route'], kind: '数据资源', order: 322 },
  '/engineering/route-steps': { routes: ['/engineering/workbench'], tables: ['eng_route_step_bind'], kind: '数据资源', order: 323 },
  '/costing': { kind: '一级菜单', order: 40 },
  '/costing/lcc-financial-baselines': {
    routes: ['/costing/lcc-financial-baselines'],
    tables: ['eng_lcc_financial_baseline'],
    kind: '页面/数据资源',
    order: 41,
  },
  '/costing/snapshot-center': {
    routes: ['/costing/snapshot-center'],
    tables: ['eng_model_snapshot'],
    kind: '页面',
    order: 42,
  },
  '/costing/decision-center': {
    routes: ['/costing/decision-center'],
    tables: ['eng_model_snapshot'],
    kind: '页面',
    order: 43,
  },
  '/engineering/snapshots': {
    routes: ['/costing/snapshot-center', '/costing/decision-center'],
    tables: ['eng_model_snapshot'],
    kind: '数据资源',
    order: 421,
  },
  '/costing/static': {
    routes: ['/costing/decision-center'],
    tables: ['eng_model_snapshot'],
    kind: '分析资源',
    order: 431,
  },
  '/system': { kind: '一级菜单', order: 50 },
  '/system/users': { routes: ['/system/users'], tables: ['sys_user', 'sys_user_role'], kind: '页面/数据资源', order: 51 },
  '/system/departments': { routes: ['/system/users'], tables: ['org_department'], kind: '数据资源', order: 511 },
  '/system/dictionaries': { routes: ['/system/dictionaries'], tables: ['sys_dict_type', 'sys_dict_item'], kind: '页面/数据资源', order: 52 },
  '/system/permissions': { routes: ['/system/permissions'], tables: ['sys_permission'], kind: '页面/数据资源', order: 53 },
  '/system/roles': { routes: ['/system/roles'], tables: ['sys_role', 'sys_role_permission'], kind: '页面/数据资源', order: 54 },
  '/system/audit-logs': { routes: ['/system/audit'], tables: ['sys_audit_log'], kind: '页面/数据资源', order: 55 },
}

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
const filterText = ref('')
const treeRef = ref<TreeInstance>()

const permissionTree = computed<PermissionTreeNode[]>(() => buildPermissionTree(permissionList.value))
const parentNameMap = computed<Record<number, string>>(() => Object.fromEntries(permissionList.value.map((item) => [item.id, item.name])))

watch(filterText, (value) => {
  treeRef.value?.filter(value)
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
  return resolveDictionaryTagType(permissionActionOptions.value, action)
}

function getActionLabel(action: PermissionAction) {
  return resolveDictionaryLabel(permissionActionOptions.value, action, action)
}

function getPermissionMeta(permission: Permission) {
  return PERMISSION_META_BY_RESOURCE[permission.resource] ?? {}
}

function getNodeType(permission: Permission): PermissionNodeType {
  if (permission.code.startsWith('MENU_')) {
    return 'menu'
  }
  if (permission.code.startsWith('PAGE_')) {
    return 'page'
  }
  if (permission.action !== 'read') {
    return 'action'
  }
  return 'resource'
}

function getNodeKind(permission: Permission) {
  const nodeType = getNodeType(permission)
  if (nodeType === 'menu') {
    return '一级菜单'
  }
  if (nodeType === 'page') {
    return '页面'
  }
  if (nodeType === 'action') {
    return '按钮权限'
  }
  return getPermissionMeta(permission).kind ?? '数据资源'
}

function getNodeIcon(permission: PermissionTreeNode) {
  if (permission.node_type === 'menu') {
    return Folder
  }
  if (permission.node_type === 'page') {
    return Document
  }
  if (permission.node_type === 'action') {
    return Pointer
  }
  return Coin
}

function getRouteText(permission: Permission) {
  const routes = getPermissionMeta(permission).routes
  return routes && routes.length > 0 ? routes.join('、') : '—'
}

function getTableText(permission: Permission) {
  const tables = getPermissionMeta(permission).tables
  return tables && tables.length > 0 ? tables.join('、') : '—'
}

function getSortWeight(permission: Permission) {
  const explicitOrder = getPermissionMeta(permission).order
  if (typeof explicitOrder === 'number') {
    return explicitOrder
  }

  const actionBase = resolveDictionarySortOrder(permissionActionOptions.value, permission.action, 999)
  return actionBase * 1000
}

function filterNode(value: string, data: PermissionTreeNode) {
  if (!value) {
    return true
  }
  return data.name.toLowerCase().includes(value.trim().toLowerCase())
}

function buildPermissionTree(items: Permission[]): PermissionTreeNode[] {
  const nodes = items.map((item) => ({
    ...item,
    node_type: getNodeType(item),
    children: [] as PermissionTreeNode[],
  }))
  const nodeMap = new Map(nodes.map((node) => [node.id, node]))

  for (const node of nodes) {
    if (node.parent_id && nodeMap.has(node.parent_id)) {
      nodeMap.get(node.parent_id)!.children.push(node)
    }
  }

  const roots = nodes.filter((node) => !node.parent_id || !nodeMap.has(node.parent_id))

  const sortTree = (treeNodes: PermissionTreeNode[]) => {
    treeNodes.sort((left, right) => {
      const weightDiff = getSortWeight(left) - getSortWeight(right)
      if (weightDiff !== 0) {
        return weightDiff
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