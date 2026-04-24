<template>
  <div class="flex flex-col md:flex-row gap-4 h-full w-full min-h-0">
    <el-card class="w-full md:w-72 flex-shrink-0 flex flex-col h-[300px] md:h-auto" shadow="never" :body-style="{ padding: '12px', flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column' }">
      <template #header>
        <div class="flex items-center justify-between">
          <span class="text-sm font-medium">工艺树</span>
        </div>
      </template>

      <el-scrollbar class="flex-1 min-h-0">
        <el-tree
          v-if="processTree.length > 0"
          :data="processTree"
          node-key="key"
          default-expand-all
          highlight-current
          :expand-on-click-node="false"
          :current-node-key="selectedTreeNodeKey"
          :props="{ children: 'children', label: 'name' }"
          class="category-tree"
          @node-click="handleTreeNodeClick"
        >
          <template #default="{ data }">
            <div class="flex items-center justify-between w-full gap-2 pr-1 py-1 text-sm">
              <div class="flex min-w-0 items-center gap-2">
                <span
                  class="flex h-5 w-5 flex-none items-center justify-center rounded-full text-[11px] font-semibold"
                  :class="
                    data.nodeType === 'root'
                      ? 'bg-slate-800 text-white'
                      : data.nodeType === 'category'
                        ? 'border border-amber-200 bg-amber-50 text-amber-700'
                        : 'border border-sky-200 bg-sky-50 text-sky-700'
                  "
                >
                  {{ data.nodeType === 'root' ? '总' : data.nodeType === 'category' ? '类' : '工' }}
                </span>
                <div class="flex min-w-0 items-center gap-2">
                  <span class="truncate" :class="data.nodeType === 'root' ? 'font-semibold text-slate-800' : 'text-slate-700'">
                    {{ data.name }}
                  </span>
                  <span v-if="data.nodeType === 'category'" class="text-xs text-slate-400">分类</span>
                  <span v-else-if="data.nodeType === 'process'" class="text-xs text-slate-400">工艺</span>
                </div>
              </div>
              <div class="flex flex-none items-center gap-1">
                <el-tag v-if="data.nodeType === 'root'" size="small" type="primary" effect="light">
                  {{ data.categoryCount ?? 0 }} 类
                </el-tag>
                <el-tag
                  v-if="data.nodeType === 'root' && (data.uncategorizedCount ?? 0) > 0"
                  size="small"
                  type="warning"
                  effect="light"
                >
                  {{ data.uncategorizedCount }} 未归类
                </el-tag>
                <el-tag
                  v-if="typeof data.count === 'number' && data.nodeType !== 'process'"
                  size="small"
                  :type="data.nodeType === 'root' ? 'success' : 'info'"
                  effect="plain"
                >
                  {{ data.count }} 项
                </el-tag>
              </div>
            </div>
          </template>
        </el-tree>
        <el-empty v-else :image-size="48" description="暂无工艺结构" />
      </el-scrollbar>
    </el-card>

    <div class="flex-1 flex flex-col gap-3 min-w-0">
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
          <el-table-column label="分类" width="140">
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
      @success="handleDialogSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref, reactive, onMounted } from 'vue'
import { Plus, Search } from '@element-plus/icons-vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import { resourceCategoryApi, processApi, ResourceType } from '@/api/masterData'
import type { ResourceCategoryTree, Process, ProcessQuery } from '@/api/masterData'
import ProcessFormDialog from '@/components/master-data/ProcessFormDialog.vue'
import { formatDate } from '@/utils/format'

type ProcessTreeNodeType = 'root' | 'category' | 'process'

interface ProcessTreeNode {
  key: string
  name: string
  nodeType: ProcessTreeNodeType
  categoryId?: number
  processId?: number
  categoryCount?: number
  uncategorizedCount?: number
  count?: number
  children?: ProcessTreeNode[]
}

const loading = ref(false)
const dialogVisible = ref(false)
const processList = ref<Process[]>([])
const categoryTree = ref<ResourceCategoryTree[]>([])
const treeProcesses = ref<Process[]>([])
const total = ref(0)
const currentProcess = ref<Process | null>(null)
const selectedTreeNodeKey = ref('process-root')

const queryState = reactive<ProcessQuery>({
  keyword: '',
  category_id: undefined,
  is_active: undefined,
  page: 1,
  size: 20,
})

const processTree = computed<ProcessTreeNode[]>(() => {
  const categoryProcessMap = new Map<number, Process[]>()
  const uncategorizedProcesses: Process[] = []

  for (const item of treeProcesses.value) {
    if (item.category_id) {
      if (!categoryProcessMap.has(item.category_id)) {
        categoryProcessMap.set(item.category_id, [])
      }
      categoryProcessMap.get(item.category_id)?.push(item)
    } else {
      uncategorizedProcesses.push(item)
    }
  }

  const categoryNodes = categoryTree.value.map<ProcessTreeNode>((category) => {
    const processChildren = (categoryProcessMap.get(category.id) || [])
      .slice()
      .sort((left, right) => left.name.localeCompare(right.name, 'zh-CN'))
      .map<ProcessTreeNode>((item) => ({
        key: `process-${item.id}`,
        name: item.name,
        nodeType: 'process',
        categoryId: category.id,
        processId: item.id,
      }))

    return {
      key: `category-${category.id}`,
      name: category.name,
      nodeType: 'category',
      categoryId: category.id,
      count: processChildren.length,
      children: processChildren,
    }
  })

  if (uncategorizedProcesses.length > 0) {
    categoryNodes.push({
      key: 'category-uncategorized',
      name: '未分类工艺',
      nodeType: 'category',
      count: uncategorizedProcesses.length,
      children: uncategorizedProcesses
        .slice()
        .sort((left, right) => left.name.localeCompare(right.name, 'zh-CN'))
        .map<ProcessTreeNode>((item) => ({
          key: `process-${item.id}`,
          name: item.name,
          nodeType: 'process',
          processId: item.id,
        })),
    })
  }

  return [
    {
      key: 'process-root',
      name: '工艺',
      nodeType: 'root',
      categoryCount: categoryTree.value.length,
      uncategorizedCount: uncategorizedProcesses.length,
      count: treeProcesses.value.length,
      children: categoryNodes,
    },
  ]
})

async function loadCategoryTree() {
  try {
    const res = await resourceCategoryApi.tree(ResourceType.PROCESS)
    categoryTree.value = res.data
  } catch (err) {
    console.error('Failed to load category tree:', err)
  }
}

async function loadTreeProcesses() {
  try {
    const res = await processApi.list({ page: 1, size: 1000 })
    treeProcesses.value = res.data.items || []
  } catch (error) {
    console.error('Failed to load process tree items:', error)
  }
}

function handleTreeNodeClick(node: ProcessTreeNode) {
  selectedTreeNodeKey.value = node.key

  if (node.nodeType === 'root') {
    queryState.category_id = undefined
  } else {
    queryState.category_id = node.categoryId
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
  void fetchData()
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
    await Promise.all([fetchData(), loadTreeProcesses()])
  } catch (error) {
    if (error === 'cancel' || error === 'close') {
      return
    }
    console.error('Delete failed:', error)
  }
}

async function handleDialogSuccess() {
  await Promise.all([fetchData(), loadTreeProcesses()])
}

onMounted(() => {
  void Promise.all([loadCategoryTree(), loadTreeProcesses(), fetchData()])
})
</script>

<style scoped>
.category-tree {
  --el-tree-node-hover-bg-color: #f3f4f6;
  --el-tree-text-color: #374151;
}

:deep(.el-tree-node__content) {
  height: 36px;
}

:deep(.el-tree-node.is-current > .el-tree-node__content) {
  background-color: var(--el-color-primary-light-9) !important;
  color: var(--el-color-primary);
  font-weight: 500;
}
</style>
