<template>
  <div class="flex flex-col md:flex-row gap-4 h-full w-full min-h-0">
    <!-- 左侧分类树 -->
    <el-card class="w-full md:w-64 flex-shrink-0 flex flex-col h-[300px] md:h-auto" shadow="never" :body-style="{ padding: '12px', flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column' }">
      <template #header>
        <div class="flex items-center justify-between">
          <span class="text-sm font-medium">工序分类</span>
        </div>
      </template>

      <el-scrollbar class="flex-1 min-h-0">
        <el-tree
          v-if="categoryTree.length > 0"
          :data="categoryTree"
          node-key="id"
          default-expand-all
          highlight-current
          :expand-on-click-node="false"
          :current-node-key="queryState.category_id ?? undefined"
          :props="{ children: 'children', label: 'name' }"
          class="category-tree"
          @node-click="handleCategoryNodeClick"
        >
          <template #default="{ data }">
            <div class="flex items-center justify-between w-full gap-2 pr-1 text-sm">
              <span class="truncate">{{ data.name }}</span>
            </div>
          </template>
        </el-tree>
        <el-empty v-else :image-size="48" description="暂无分类" />
      </el-scrollbar>
    </el-card>

    <!-- 右侧内容区 -->
    <div class="flex-1 flex flex-col gap-3 min-w-0">
      <!-- 搜索栏 -->
      <el-card shadow="never" body-style="padding:12px 16px">
        <div class="flex items-center gap-3">
          <el-input
            v-model="queryState.keyword"
            placeholder="搜索工序名称 / 编码"
            :prefix-icon="Search"
            clearable
            class="w-64"
            @change="handleSearch"
            @keyup.enter="handleSearch"
          />
          <el-select v-model="queryState.is_active" placeholder="启用状态" clearable class="w-32" @change="handleSearch">
            <el-option label="启用" :value="true" />
            <el-option label="禁用" :value="false" />
          </el-select>
          <div class="flex-1" />
          <el-button type="primary" :icon="Plus" @click="openCreateDialog">新建工艺</el-button>
        </div>
      </el-card>

      <!-- 表格区 -->
      <el-card shadow="never" class="flex-1 flex flex-col min-h-0" :body-style="{ padding: '0', display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0 }">
        <el-table
          v-loading="loading"
          :data="processList"
          stripe
          class="w-full flex-1"
          height="100%"
        >
          <el-table-column prop="code" label="编码" width="130" />
          <el-table-column prop="name" label="名称" min-width="140" show-overflow-tooltip />
          <el-table-column label="分类" width="120">
            <template #default="{ row }">
              <span v-if="row.category">{{ row.category.name }}</span>
              <span v-else class="text-gray-400">-</span>
            </template>
          </el-table-column>
          <el-table-column label="准备工时(h)" width="110" align="right">
            <template #default="{ row }">
              <span v-if="row.setup_time !== null">{{ row.setup_time }}</span>
              <span v-else class="text-gray-400">-</span>
            </template>
          </el-table-column>
          <el-table-column label="标准工时(h)" width="110" align="right">
            <template #default="{ row }">
              <span v-if="row.standard_time !== null">{{ row.standard_time }}</span>
              <span v-else class="text-gray-400">-</span>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="80" align="center">
            <template #default="{ row }">
              <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
                {{ row.is_active ? '启用' : '禁用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="170">
            <template #default="{ row }">
              {{ formatDate(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="140" fixed="right" align="center">
            <template #default="{ row }">
              <el-button link type="primary" @click="openEditDialog(row)">编辑</el-button>
              <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>

        <div class="p-3 border-t border-gray-100 bg-white flex justify-end flex-shrink-0">
          <el-pagination
            v-model:current-page="queryState.page"
            v-model:page-size="queryState.size"
            :total="total"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next"
            @size-change="handleSearch"
            @current-change="fetchData"
          />
        </div>
      </el-card>
    </div>

    <ProcessFormDialog
      v-model="dialogVisible"
      :data="currentProcess"
      :category-tree="categoryTree"
      @success="handleSearch"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { Plus, Search } from '@element-plus/icons-vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import { resourceCategoryApi, processApi } from '@/api/masterData'
import type { ResourceCategory, Process, ProcessQuery } from '@/api/masterData'
import ProcessFormDialog from '@/components/master-data/ProcessFormDialog.vue'

const loading = ref(false)
const dialogVisible = ref(false)
const processList = ref<Process[]>([])
const categoryTree = ref<ResourceCategory[]>([])
const total = ref(0)
const currentProcess = ref<Process | null>(null)

const queryState = reactive<ProcessQuery>({
  keyword: '',
  category_id: undefined,
  is_active: undefined,
  page: 1,
  size: 20
})

function formatDate(dateStr: string) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

async function loadCategoryTree() {
  try {
    const res = await resourceCategoryApi.tree('PROCESS')
    categoryTree.value = res.data
  } catch (err) {
    console.error('Failed to load category tree:', err)
  }
}

function handleCategoryNodeClick(node: ResourceCategory) {
  if (queryState.category_id === node.id) {
    queryState.category_id = undefined
  } else {
    queryState.category_id = node.id
  }
  handleSearch()
}

async function fetchData() {
  loading.value = true
  try {
    const res = await processApi.list(queryState)
    processList.value = res.data.items || []
    total.value = res.data.total || 0
  } catch (error) {
    console.error('Failed to fetch process data:', error)
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  queryState.page = 1
  fetchData()
}

function openCreateDialog() {
  currentProcess.value = null
  dialogVisible.value = true
}

function openEditDialog(row: Process) {
  currentProcess.value = JSON.parse(JSON.stringify(row))
  dialogVisible.value = true
}

async function handleDelete(row: Process) {
  try {
    await ElMessageBox.confirm(`确定要删除工序 [${row.name}] 吗？删除后不可恢复。`, '危险操作', {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning',
      center: true,
    })
    await processApi.remove(row.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch (error) {
    if (error === 'cancel' || error === 'close') {
      return
    }
    console.error('Delete failed:', error)
  }
}

onMounted(() => {
  loadCategoryTree()
  fetchData()
})
</script>

<style scoped>
.category-tree {
  --el-tree-node-hover-bg-color: #f3f4f6;
  --el-tree-text-color: #374151;
}

:deep(.el-tree-node__content) {
  height: 32px;
}

:deep(.el-tree-node.is-current > .el-tree-node__content) {
  background-color: var(--el-color-primary-light-9) !important;
  color: var(--el-color-primary);
  font-weight: 500;
}
</style>
