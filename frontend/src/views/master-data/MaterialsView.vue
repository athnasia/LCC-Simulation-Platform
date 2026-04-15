<template>
  <div class="flex flex-col md:flex-row gap-4 h-full w-full min-h-0">
    <el-card class="w-full md:w-64 flex-shrink-0 flex flex-col h-[300px] md:h-auto" shadow="never" :body-style="{ padding: '12px', flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column' }">
      <template #header>
        <div class="flex items-center justify-between">
          <span class="text-sm font-medium">材料分类</span>
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
          :current-node-key="queryState.categoryId ?? undefined"
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

    <div class="flex-1 flex flex-col gap-3 min-w-0">
      <el-card shadow="never" body-style="padding:12px 16px">
        <div class="flex items-center gap-3">
          <el-input
            v-model="queryState.keyword"
            placeholder="搜索材料名称 / 编码"
            :prefix-icon="Search"
            clearable
            class="w-64"
            @change="loadMaterials"
          />
          <el-select v-model="queryState.isActive" placeholder="启用状态" clearable class="w-32" @change="loadMaterials">
            <el-option label="启用" :value="true" />
            <el-option label="禁用" :value="false" />
          </el-select>
          <div class="flex-1" />
          <el-button v-if="canWrite" type="primary" :icon="Plus" @click="openMaterialDialog()">新建材料</el-button>
        </div>
      </el-card>

      <el-card shadow="never" class="flex-1 flex flex-col min-h-0" :body-style="{ padding: '0', display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0 }">
        <el-table
          v-loading="tableLoading"
          :data="materialList"
          stripe
          class="w-full flex-1"
          height="100%"
        >
          <el-table-column prop="code" label="编码" width="120" />
          <el-table-column prop="name" label="名称" min-width="140" show-overflow-tooltip />
          <el-table-column label="分类" width="120">
            <template #default="{ row }">
              <span v-if="row.category">{{ row.category.name }}</span>
              <span v-else class="text-gray-400">-</span>
            </template>
          </el-table-column>
          <el-table-column label="单价" width="120" align="right">
            <template #default="{ row }">
              <span v-if="row.unit_price !== null">{{ formatPrice(row.unit_price) }}</span>
              <span v-else class="text-gray-400">-</span>
            </template>
          </el-table-column>
          <el-table-column label="计价单位" width="100">
            <template #default="{ row }">
              <span v-if="row.pricing_unit">{{ row.pricing_unit.symbol }}</span>
              <span v-else class="text-gray-400">-</span>
            </template>
          </el-table-column>
          <el-table-column label="消耗单位" width="100">
            <template #default="{ row }">
              <span v-if="row.consumption_unit">{{ row.consumption_unit.symbol }}</span>
              <span v-else class="text-gray-400">-</span>
            </template>
          </el-table-column>
          <el-table-column label="损耗率" width="80" align="right">
            <template #default="{ row }">
              <span v-if="row.loss_rate !== null">{{ row.loss_rate }}%</span>
              <span v-else class="text-gray-400">-</span>
            </template>
          </el-table-column>
          <el-table-column label="柔性属性" min-width="160">
            <template #default="{ row }">
              <template v-if="row.dynamic_attributes && Object.keys(row.dynamic_attributes).length > 0">
                <el-popover
                  placement="top"
                  :width="300"
                  trigger="hover"
                >
                  <template #reference>
                    <div class="flex flex-wrap gap-1 cursor-pointer">
                      <el-tag
                        v-for="(value, key) in getDisplayAttrs(row.dynamic_attributes)"
                        :key="key"
                        size="small"
                        type="info"
                      >
                        {{ key }}: {{ value }}
                      </el-tag>
                      <el-tag
                        v-if="Object.keys(row.dynamic_attributes).length > 3"
                        size="small"
                        type="info"
                      >
                        +{{ Object.keys(row.dynamic_attributes).length - 3 }}
                      </el-tag>
                    </div>
                  </template>
                  <div class="text-sm">
                    <div
                      v-for="(value, key) in row.dynamic_attributes"
                      :key="key"
                      class="py-1 border-b border-gray-100 last:border-0"
                    >
                      <span class="font-medium text-gray-600">{{ key }}:</span>
                      <span class="ml-2">{{ formatAttrValue(value) }}</span>
                    </div>
                  </div>
                </el-popover>
              </template>
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
          <el-table-column label="操作" width="140" fixed="right">
            <template #default="{ row }">
              <el-button v-if="canWrite" link type="primary" @click="openMaterialDialog(row)">编辑</el-button>
              <el-button v-if="canDelete" link type="danger" @click="deleteMaterial(row)">删除</el-button>
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
            @change="loadMaterials"
          />
        </div>
      </el-card>
    </div>

    <MaterialFormDialog
      v-model="materialDialogVisible"
      :data="currentMaterial"
      :category-tree="categoryTree"
      @success="loadMaterials"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import { materialApi, resourceCategoryApi, ResourceType } from '@/api/masterData'
import type { Material, MaterialQuery, ResourceCategoryTree } from '@/api/masterData'
import MaterialFormDialog from '@/components/master-data/MaterialFormDialog.vue'
import { useAuthStore } from '@/stores/auth'

interface MaterialQueryState {
  keyword: string
  isActive: boolean | null
  categoryId: number | null
}

const authStore = useAuthStore()
const canWrite = computed(() => authStore.hasPermissionScope('/master-data/materials:write'))
const canDelete = computed(() => authStore.hasPermissionScope('/master-data/materials:delete'))

const categoryTree = ref<ResourceCategoryTree[]>([])
const materialList = ref<Material[]>([])
const tableLoading = ref(false)
const pagination = reactive({ page: 1, size: 20, total: 0 })
const queryState = reactive<MaterialQueryState>({
  keyword: '',
  isActive: null,
  categoryId: null,
})

const materialDialogVisible = ref(false)
const currentMaterial = ref<Material | null>(null)

async function loadCategories() {
  const res = await resourceCategoryApi.tree(ResourceType.MATERIAL)
  categoryTree.value = res.data
}

function handleCategoryNodeClick(node: ResourceCategoryTree) {
  if (queryState.categoryId === node.id) {
    queryState.categoryId = null
  } else {
    queryState.categoryId = node.id
  }
  pagination.page = 1
  loadMaterials()
}

async function loadMaterials() {
  tableLoading.value = true
  try {
    const params: MaterialQuery = {
      page: pagination.page,
      size: pagination.size,
    }
    if (queryState.keyword) {
      params.keyword = queryState.keyword
    }
    if (queryState.isActive !== null) {
      params.is_active = queryState.isActive
    }
    if (queryState.categoryId !== null) {
      params.category_id = queryState.categoryId
    }

    const res = await materialApi.list(params)
    materialList.value = res.data.items
    pagination.total = res.data.total
  } finally {
    tableLoading.value = false
  }
}

async function openMaterialDialog(row?: Material) {
  if (row) {
    const detail = await materialApi.detail(row.id)
    currentMaterial.value = detail.data
  } else {
    currentMaterial.value = null
  }
  materialDialogVisible.value = true
}

async function deleteMaterial(row: Material) {
  try {
    await ElMessageBox.confirm(`确定删除材料「${row.name}（${row.code}）」吗？`, '警告', {
      type: 'warning',
    })
    await materialApi.remove(row.id)
    ElMessage.success('已删除')
    await loadMaterials()
  } catch (error: unknown) {
    if (error === 'cancel' || error === 'close') {
      return
    }
    ElMessage.error('删除失败，请稍后重试')
  }
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleString('zh-CN', { hour12: false })
}

function formatPrice(value: number | string | null) {
  if (value === null || value === undefined) return '-'
  return `¥${Number(value).toFixed(4)}`
}

function getDisplayAttrs(attrs: Record<string, unknown>): Record<string, unknown> {
  const keys = Object.keys(attrs).slice(0, 3)
  const result: Record<string, unknown> = {}
  for (const key of keys) {
    result[key] = attrs[key]
  }
  return result
}

function formatAttrValue(value: unknown): string {
  if (typeof value === 'number') {
    return String(value)
  }
  return String(value)
}

onMounted(() => {
  loadCategories()
  loadMaterials()
})
</script>

<style scoped>
.category-tree :deep(.el-tree-node__content) {
  height: 34px;
  border-radius: 8px;
}

.category-tree :deep(.el-tree-node__content:hover) {
  background-color: #f9fafb;
}

.category-tree :deep(.el-tree--highlight-current .el-tree-node.is-current > .el-tree-node__content) {
  background-color: #eef2ff;
  color: #4f46e5;
}
</style>
