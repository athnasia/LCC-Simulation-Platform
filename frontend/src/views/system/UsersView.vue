<template>
  <div class="flex gap-4 h-full">
    <!-- ── 左：部门树 ─────────────────────────────── -->
    <el-card v-if="canReadDepartments" class="w-56 flex-shrink-0" shadow="never" body-style="padding:12px">
      <template #header>
        <div class="flex items-center justify-between">
          <span class="text-sm font-medium">部门列表</span>
          <el-button v-if="canWriteDepartments" link type="primary" :icon="Plus" @click="openDeptDialog()">新建</el-button>
        </div>
      </template>

      <el-scrollbar max-height="calc(100vh - 220px)">
        <el-tree
          v-if="deptTree.length > 0"
          :data="deptTree"
          node-key="id"
          default-expand-all
          highlight-current
          :expand-on-click-node="false"
          :current-node-key="selectedDeptId ?? undefined"
          :props="{ children: 'children', label: 'name' }"
          class="dept-tree"
          @node-click="handleDeptNodeClick"
        >
          <template #default="{ data }">
            <div class="flex items-center justify-between w-full gap-2 pr-1 text-sm">
              <span class="truncate">{{ data.name }}</span>
              <div
                v-if="canWriteDepartments || canDeleteDepartments"
                class="flex-shrink-0 flex gap-1 dept-ops"
              >
                <el-button
                  v-if="canWriteDepartments"
                  link
                  size="small"
                  :icon="Edit"
                  @click.stop="openDeptDialog(data)"
                />
                <el-button
                  v-if="canDeleteDepartments"
                  link
                  size="small"
                  :icon="Delete"
                  type="danger"
                  @click.stop="deleteDept(data)"
                />
              </div>
            </div>
          </template>
        </el-tree>
        <el-empty v-else :image-size="48" description="暂无部门" />
      </el-scrollbar>
    </el-card>

    <!-- ── 右：用户表格 ───────────────────────────── -->
    <div class="flex-1 flex flex-col gap-3 min-w-0">
      <!-- 工具栏 -->
      <el-card shadow="never" body-style="padding:12px 16px">
        <div class="flex items-center gap-3">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索用户名 / 姓名 / 邮箱"
            :prefix-icon="Search"
            clearable
            class="w-64"
            @change="loadUsers"
          />
          <el-select v-model="filterActive" placeholder="账号状态" clearable class="w-32" @change="loadUsers">
            <el-option label="启用" :value="true" />
            <el-option label="禁用" :value="false" />
          </el-select>
          <div class="flex-1" />
          <el-button v-if="canWriteUsers" type="primary" :icon="Plus" @click="openUserDialog()">新建用户</el-button>
        </div>
      </el-card>

      <!-- 表格 -->
      <el-card shadow="never" class="flex-1" body-style="padding:0">
        <el-table
          v-loading="tableLoading"
          :data="userList"
          stripe
          class="w-full"
          @sort-change="loadUsers"
        >
          <el-table-column prop="username" label="用户名" width="130" />
          <el-table-column prop="real_name" label="姓名" width="100" />
          <el-table-column prop="email" label="邮箱" min-width="160" show-overflow-tooltip />
          <el-table-column prop="phone" label="手机号" width="130" />
          <el-table-column label="状态" width="80" align="center">
            <template #default="{ row }">
              <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
                {{ row.is_active ? '启用' : '禁用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="170" sortable>
            <template #default="{ row }">
              {{ formatDate(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="180" fixed="right">
            <template #default="{ row }">
              <el-button v-if="canWriteUsers" link type="primary" @click="openUserDialog(row)">编辑</el-button>
              <el-button v-if="canAdminUsers" link type="warning" @click="openResetPwdDialog(row)">重置密码</el-button>
              <el-button v-if="canDeleteUsers" link type="danger" @click="deleteUser(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <div class="flex justify-end p-4">
          <el-pagination
            v-model:current-page="pagination.page"
            v-model:page-size="pagination.size"
            :total="pagination.total"
            :page-sizes="[10, 20, 50]"
            layout="total, sizes, prev, pager, next"
            @change="loadUsers"
          />
        </div>
      </el-card>
    </div>

    <!-- 弹窗 -->
    <DeptFormDialog
      v-model="deptDialogVisible"
      :data="currentDept"
      :parent-options="deptList"
      @success="loadDepts"
    />

    <UserFormDialog
      v-model="userDialogVisible"
      :data="currentUser"
      :dept-options="deptList"
      :role-options="roleOptions"
      @success="loadUsers"
    />

    <UserResetPwdDialog
      v-if="resetPwdDialogVisible"
      v-model="resetPwdDialogVisible"
      :user-id="currentUser!.id"
      :username="currentUser!.username"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import { Plus, Edit, Delete, Search } from '@element-plus/icons-vue'
import { deptApi, userApi, roleApi } from '@/api/system'
import type { Department, UserBase, UserDetail, RoleBase } from '@/api/system'
import DeptFormDialog from '@/components/system/DeptFormDialog.vue'
import UserFormDialog from '@/components/system/UserFormDialog.vue'
import UserResetPwdDialog from '@/components/system/UserResetPwdDialog.vue'
import { useAuthStore } from '@/stores/auth'

type DepartmentTreeNode = Department & { children: DepartmentTreeNode[] }

const authStore = useAuthStore()
const canReadDepartments = computed(() => authStore.hasPermissionScope('/system/departments:read'))
const canWriteDepartments = computed(() => authStore.hasPermissionScope('/system/departments:write'))
const canDeleteDepartments = computed(() => authStore.hasPermissionScope('/system/departments:delete'))
const canWriteUsers = computed(() => authStore.hasPermissionScope('/system/users:write'))
const canDeleteUsers = computed(() => authStore.hasPermissionScope('/system/users:delete'))
const canAdminUsers = computed(() => authStore.hasPermissionScope('/system/users:admin'))
const canReadRoles = computed(() => authStore.hasPermissionScope('/system/roles:read'))

// ── 部门 ───────────────────────────────────────────────────────
const deptList = ref<Department[]>([])
const selectedDeptId = ref<number | null>(null)
const deptDialogVisible = ref(false)
const currentDept = ref<Department | null>(null)
const deptTree = computed<DepartmentTreeNode[]>(() => buildDepartmentTree(deptList.value))

async function loadDepts() {
  if (!canReadDepartments.value) {
    deptList.value = []
    selectedDeptId.value = null
    return
  }
  const res = await deptApi.list({ size: 200 })
  deptList.value = res.data.items
}

function selectDept(id: number) {
  selectedDeptId.value = selectedDeptId.value === id ? null : id
  pagination.page = 1
  loadUsers()
}

function handleDeptNodeClick(dept: DepartmentTreeNode) {
  selectDept(dept.id)
}

function openDeptDialog(dept?: Department) {
  currentDept.value = dept ?? null
  deptDialogVisible.value = true
}

async function deleteDept(dept: Department) {
  await ElMessageBox.confirm(`确定删除部门「${dept.name}」吗？`, '警告', { type: 'warning' })
  await deptApi.remove(dept.id)
  ElMessage.success('已删除')
  loadDepts()
}

// ── 用户 ───────────────────────────────────────────────────────
const userList = ref<UserBase[]>([])
const tableLoading = ref(false)
const searchKeyword = ref('')
const filterActive = ref<boolean | null>(null)
const pagination = reactive({ page: 1, size: 20, total: 0 })

const userDialogVisible = ref(false)
const resetPwdDialogVisible = ref(false)
const currentUser = ref<UserDetail | null>(null)
const roleOptions = ref<RoleBase[]>([])

async function loadUsers() {
  tableLoading.value = true
  try {
    const params: Record<string, unknown> = {
      page: pagination.page,
      size: pagination.size,
    }
    if (searchKeyword.value) params.keyword = searchKeyword.value
    if (filterActive.value !== null) params.is_active = filterActive.value
    if (selectedDeptId.value) params.department_id = selectedDeptId.value

    const res = await userApi.list(params)
    userList.value = res.data.items
    pagination.total = res.data.total
  } finally {
    tableLoading.value = false
  }
}

async function openUserDialog(row?: UserBase) {
  if (row) {
    const detail = await userApi.detail(row.id)
    currentUser.value = detail.data
  } else {
    currentUser.value = null
  }
  userDialogVisible.value = true
}

async function openResetPwdDialog(row: UserBase) {
  const detail = await userApi.detail(row.id)
  currentUser.value = detail.data
  resetPwdDialogVisible.value = true
}

async function deleteUser(row: UserBase) {
  await ElMessageBox.confirm(`确定删除用户「${row.real_name}（${row.username}）」吗？`, '警告', {
    type: 'warning',
  })
  await userApi.remove(row.id)
  ElMessage.success('已删除')
  loadUsers()
}

async function loadRoleOptions() {
  if (!canReadRoles.value) {
    roleOptions.value = []
    return
  }
  const res = await roleApi.list({ size: 200 })
  roleOptions.value = res.data.items
}

// ── 工具函数 ───────────────────────────────────────────────────
function formatDate(iso: string) {
  return new Date(iso).toLocaleString('zh-CN', { hour12: false })
}

function buildDepartmentTree(items: Department[]): DepartmentTreeNode[] {
  const nodeMap = new Map<number, DepartmentTreeNode>()
  const roots: DepartmentTreeNode[] = []

  const sortedItems = [...items].sort((left, right) => {
    if (left.sort_order !== right.sort_order) {
      return left.sort_order - right.sort_order
    }
    return left.id - right.id
  })

  for (const item of sortedItems) {
    nodeMap.set(item.id, { ...item, children: [] })
  }

  for (const item of sortedItems) {
    const node = nodeMap.get(item.id)!
    if (item.parent_id && nodeMap.has(item.parent_id)) {
      nodeMap.get(item.parent_id)!.children.push(node)
      continue
    }
    roots.push(node)
  }

  return roots
}

onMounted(() => {
  loadDepts()
  loadUsers()
  loadRoleOptions()
})
</script>

<style scoped>
.dept-tree :deep(.el-tree-node__content) {
  height: 34px;
  border-radius: 8px;
}

.dept-tree :deep(.el-tree-node__content:hover) {
  background-color: #f9fafb;
}

.dept-tree :deep(.el-tree--highlight-current .el-tree-node.is-current > .el-tree-node__content) {
  background-color: #eef2ff;
  color: #4f46e5;
}

.dept-tree :deep(.el-tree-node__content:hover .dept-ops) {
  opacity: 1;
}

.dept-ops {
  opacity: 0;
}
</style>

