<template>
  <div class="flex flex-col gap-3">
    <!-- 工具栏 -->
    <el-card shadow="never" body-style="padding:12px 16px">
      <div class="flex items-center gap-3">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索角色名称或编码"
          :prefix-icon="Search"
          clearable
          class="w-64"
          @change="loadRoles"
        />
        <el-select v-model="filterActive" placeholder="状态" clearable class="w-28" @change="loadRoles">
          <el-option label="启用" :value="true" />
          <el-option label="禁用" :value="false" />
        </el-select>
        <div class="flex-1" />
        <el-button v-if="canWriteRoles" type="primary" :icon="Plus" @click="openDialog()">新建角色</el-button>
      </div>
    </el-card>

    <!-- 表格 -->
    <el-card shadow="never" body-style="padding:0">
      <el-table v-loading="loading" :data="roleList" stripe class="w-full">
        <el-table-column prop="name" label="角色名称" width="180" />
        <el-table-column prop="code" label="角色编码" width="180">
          <template #default="{ row }">
            <el-tag size="small" type="info">{{ row.code }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button v-if="canWriteRoles" link type="primary" @click="openDialog(row)">编辑</el-button>
            <el-button link @click="viewPermissions(row)">查看权限</el-button>
            <el-button v-if="canDeleteRoles" link type="danger" @click="deleteRole(row)">删除</el-button>
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
          @change="loadRoles"
        />
      </div>
    </el-card>

    <!-- 权限详情抽屉 -->
    <el-drawer v-model="drawerVisible" :title="`角色「${drawerRole?.name}」— 权限列表`" size="380px">
      <div v-if="drawerLoading" class="flex justify-center py-8">
        <el-icon class="is-loading" :size="24"><Loading /></el-icon>
      </div>
      <template v-else>
        <el-empty v-if="drawerPermissions.length === 0" description="该角色暂未绑定任何权限" />
        <div v-else class="flex flex-col gap-2">
          <el-card
            v-for="perm in sortedDrawerPermissions"
            :key="perm.id"
            shadow="never"
            body-style="padding:12px"
            class="!border-gray-200"
          >
            <div class="flex items-center justify-between">
              <span class="text-sm font-medium text-gray-800">{{ perm.name }}</span>
              <el-tag size="small" :type="actionTagType(perm.action)">{{ getActionLabel(perm.action) }}</el-tag>
            </div>
            <div class="text-xs text-gray-400 mt-1">{{ perm.code }}</div>
          </el-card>
        </div>
      </template>
    </el-drawer>

    <RoleFormDialog
      v-model="dialogVisible"
      :data="currentRole"
      :all-permissions="allPermissions"
      @success="loadRoles"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import { Plus, Search, Loading } from '@element-plus/icons-vue'
import { roleApi, permApi } from '@/api/system'
import type { RoleBase, RoleDetail, Permission, PermissionAction } from '@/api/system'
import RoleFormDialog from '@/components/system/RoleFormDialog.vue'
import { PERMISSION_ACTION_OPTIONS } from '@/constants/systemDictionaries'
import { useAuthStore } from '@/stores/auth'
import { useDictionaryStore } from '@/stores/dictionaries'
import { resolveDictionaryLabel, resolveDictionarySortOrder, resolveDictionaryTagType } from '@/utils/dictionaryDisplay'

const authStore = useAuthStore()
const dictionaryStore = useDictionaryStore()
const canWriteRoles = computed(() => authStore.hasPermissionScope('/system/roles:write'))
const canDeleteRoles = computed(() => authStore.hasPermissionScope('/system/roles:delete'))
const canReadPermissions = computed(() => authStore.hasPermissionScope('/system/permissions:read'))
const permissionActionOptions = computed(() => dictionaryStore.getOptions('PERMISSION_ACTION', PERMISSION_ACTION_OPTIONS))

const roleList = ref<RoleBase[]>([])
const loading = ref(false)
const searchKeyword = ref('')
const filterActive = ref<boolean | null>(null)
const pagination = reactive({ page: 1, size: 20, total: 0 })

const dialogVisible = ref(false)
const currentRole = ref<RoleDetail | null>(null)
const allPermissions = ref<Permission[]>([])

const drawerVisible = ref(false)
const drawerLoading = ref(false)
const drawerRole = ref<RoleBase | null>(null)
const drawerPermissions = ref<RoleDetail['permissions']>([])
const sortedDrawerPermissions = computed(() => {
  return [...drawerPermissions.value].sort((left, right) => {
    const actionDiff = resolveDictionarySortOrder(permissionActionOptions.value, left.action, 999)
      - resolveDictionarySortOrder(permissionActionOptions.value, right.action, 999)
    if (actionDiff !== 0) {
      return actionDiff
    }
    return left.name.localeCompare(right.name, 'zh-CN')
  })
})

async function loadRoles() {
  loading.value = true
  try {
    const res = await roleApi.list({
      page: pagination.page,
      size: pagination.size,
      keyword: searchKeyword.value || undefined,
      is_active: filterActive.value ?? undefined,
    })
    roleList.value = res.data.items
    pagination.total = res.data.total
  } finally {
    loading.value = false
  }
}

async function openDialog(row?: RoleBase) {
  if (row) {
    const res = await roleApi.detail(row.id)
    currentRole.value = res.data
  } else {
    currentRole.value = null
  }
  dialogVisible.value = true
}

async function viewPermissions(row: RoleBase) {
  drawerRole.value = row
  drawerVisible.value = true
  drawerLoading.value = true
  try {
    const res = await roleApi.detail(row.id)
    drawerPermissions.value = res.data.permissions
  } finally {
    drawerLoading.value = false
  }
}

async function deleteRole(row: RoleBase) {
  await ElMessageBox.confirm(`确定删除角色「${row.name}」吗？`, '警告', { type: 'warning' })
  await roleApi.remove(row.id)
  ElMessage.success('已删除')
  loadRoles()
}

async function loadAllPermissions() {
  if (!canReadPermissions.value || !canWriteRoles.value) {
    allPermissions.value = []
    return
  }
  const res = await permApi.list({ size: 500 })
  allPermissions.value = res.data.items
}

const actionTagType = (action: PermissionAction) => {
  return resolveDictionaryTagType(permissionActionOptions.value, action)
}

const getActionLabel = (action: PermissionAction) => {
  return resolveDictionaryLabel(permissionActionOptions.value, action, action)
}

onMounted(() => {
  loadRoles()
  loadAllPermissions()
})
</script>

