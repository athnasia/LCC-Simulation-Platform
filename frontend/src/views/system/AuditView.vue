<template>
  <div class="flex flex-col gap-3">
    <!-- 过滤器 -->
    <el-card shadow="never" body-style="padding:12px 16px">
      <div class="flex flex-wrap items-center gap-3">
        <el-select v-model="filter.action" placeholder="操作类型" clearable class="w-44">
          <el-option label="CREATE — 创建" value="CREATE" />
          <el-option label="UPDATE — 更新" value="UPDATE" />
          <el-option label="DELETE — 删除" value="DELETE" />
          <el-option label="RESET_PASSWORD — 重置密码" value="RESET_PASSWORD" />
          <el-option label="CHANGE_PASSWORD — 修改密码" value="CHANGE_PASSWORD" />
        </el-select>
        <el-select v-model="filter.resource_type" placeholder="资源类型" clearable class="w-44">
          <el-option label="OrgDepartment — 部门" value="OrgDepartment" />
          <el-option label="SysPermission — 权限" value="SysPermission" />
          <el-option label="SysRole — 角色" value="SysRole" />
          <el-option label="SysUser — 用户" value="SysUser" />
        </el-select>
        <el-date-picker
          v-model="dateRange"
          type="datetimerange"
          range-separator="至"
          start-placeholder="开始时间"
          end-placeholder="结束时间"
          value-format="YYYY-MM-DDTHH:mm:ss"
          class="w-96"
        />
        <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
        <el-button :icon="Refresh" @click="handleReset">重置</el-button>
      </div>
    </el-card>

    <!-- 表格 -->
    <el-card shadow="never" body-style="padding:0">
      <el-table v-loading="loading" :data="logList" stripe class="w-full">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="username" label="操作人" width="120" />
        <el-table-column label="操作类型" width="170">
          <template #default="{ row }">
            <el-tag :type="actionTagType(row.action)" size="small">{{ row.action }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="资源类型" width="160">
          <template #default="{ row }">
            <span class="text-sm text-gray-600">{{ row.resource_type }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="resource_id" label="资源 ID" width="100" />
        <el-table-column prop="ip_address" label="IP 地址" width="130" />
        <el-table-column prop="created_at" label="操作时间" min-width="170">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="详情" width="80" align="center">
          <template #default="{ row }">
            <el-popover
              v-if="row.detail"
              placement="left"
              :width="320"
              trigger="click"
            >
              <template #reference>
                <el-button link type="info" size="small">查看</el-button>
              </template>
              <pre class="text-xs text-gray-700 overflow-auto max-h-64 whitespace-pre-wrap">{{ JSON.stringify(row.detail, null, 2) }}</pre>
            </el-popover>
            <span v-else class="text-gray-300 text-xs">—</span>
          </template>
        </el-table-column>
      </el-table>
      <div class="flex justify-end p-4">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          @change="loadLogs"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { Search, Refresh } from '@element-plus/icons-vue'
import { auditApi } from '@/api/system'
import type { AuditLog, AuditAction } from '@/api/system'

const logList = ref<AuditLog[]>([])
const loading = ref(false)
const dateRange = ref<[string, string] | null>(null)
const pagination = reactive({ page: 1, size: 20, total: 0 })

const filter = reactive({
  action: '' as AuditAction | '',
  resource_type: '',
})

async function loadLogs() {
  loading.value = true
  try {
    const params: Record<string, unknown> = {
      page: pagination.page,
      size: pagination.size,
    }
    if (filter.action) params.action = filter.action
    if (filter.resource_type) params.resource_type = filter.resource_type
    if (dateRange.value) {
      params.start_time = dateRange.value[0]
      params.end_time = dateRange.value[1]
    }

    const res = await auditApi.list(params)
    logList.value = res.data.items
    pagination.total = res.data.total
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  pagination.page = 1
  loadLogs()
}

function handleReset() {
  filter.action = ''
  filter.resource_type = ''
  dateRange.value = null
  pagination.page = 1
  loadLogs()
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleString('zh-CN', { hour12: false })
}

const actionTagType = (action: AuditAction) => {
  const map: Record<AuditAction, '' | 'success' | 'warning' | 'danger'> = {
    CREATE: 'success',
    UPDATE: '',
    DELETE: 'danger',
    RESET_PASSWORD: 'warning',
    CHANGE_PASSWORD: 'warning',
  }
  return map[action] ?? ''
}

onMounted(loadLogs)
</script>

