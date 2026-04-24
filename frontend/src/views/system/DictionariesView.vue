<template>
  <div class="h-full">
    <el-tabs v-model="activeTab" class="dictionaries-tabs h-full">
      <el-tab-pane label="系统字典" name="system">
        <div class="tab-pane-body flex gap-4 h-full">
          <el-card class="w-[360px] flex-shrink-0" shadow="never" body-style="padding:12px">
            <template #header>
              <div class="flex items-center justify-between gap-2">
                <span class="text-sm font-medium">字典类型</span>
                <el-button v-if="canWrite" type="primary" link :icon="Plus" @click="openTypeDialog()">新建类型</el-button>
              </div>
            </template>

            <div class="mb-3 flex items-center gap-2">
              <el-input
                v-model="typeKeyword"
                placeholder="搜索名称 / 编码"
                :prefix-icon="Search"
                clearable
                @change="loadTypes"
              />
            </div>

            <el-scrollbar max-height="calc(100vh - 240px)">
              <div v-if="typeList.length > 0" class="flex flex-col gap-2 pr-1">
                <button
                  v-for="item in typeList"
                  :key="item.id"
                  type="button"
                  class="rounded-xl border p-3 text-left transition-all"
                  :class="selectedType?.id === item.id ? 'border-indigo-500 bg-indigo-50' : 'border-gray-200 bg-white hover:border-indigo-200'"
                  @click="selectType(item)"
                >
                  <div class="flex items-start justify-between gap-2">
                    <div class="min-w-0">
                      <div class="truncate text-sm font-medium text-gray-800">{{ item.name }}</div>
                      <div class="mt-1 text-xs text-gray-400 uppercase">{{ item.code }}</div>
                    </div>
                    <el-tag :type="item.is_active ? 'success' : 'info'" size="small">{{ item.is_active ? '启用' : '禁用' }}</el-tag>
                  </div>
                  <div class="mt-3 flex items-center justify-between text-xs text-gray-500">
                    <span>排序 {{ item.sort_order }}</span>
                    <span>{{ item.description || '暂无描述' }}</span>
                  </div>
                  <div v-if="canWrite || canDelete" class="mt-3 flex justify-end gap-2">
                    <el-button v-if="canWrite" link type="primary" @click.stop="openTypeDialog(item)">编辑</el-button>
                    <el-button v-if="canDelete" link type="danger" @click.stop="deleteType(item)">删除</el-button>
                  </div>
                </button>
              </div>
              <el-empty v-else description="暂无字典类型" :image-size="56" />
            </el-scrollbar>
          </el-card>

          <div class="flex-1 flex flex-col gap-3 min-w-0">
            <el-card shadow="never" body-style="padding:12px 16px">
              <div class="flex items-center gap-3">
                <el-input
                  v-model="itemKeyword"
                  placeholder="搜索存储值 / 显示标签"
                  :prefix-icon="Search"
                  clearable
                  class="w-72"
                  @change="handleItemFilter"
                />
                <el-select v-model="itemActive" placeholder="状态" clearable class="w-28" @change="handleItemFilter">
                  <el-option label="启用" :value="true" />
                  <el-option label="禁用" :value="false" />
                </el-select>
                <div class="flex-1" />
                <el-button v-if="canWrite" type="primary" :icon="Plus" :disabled="!selectedType" @click="openItemDialog()">新建字典项</el-button>
              </div>
            </el-card>

            <el-card shadow="never" class="flex-1" body-style="padding:0">
              <template #header>
                <div class="flex items-center justify-between">
                  <span class="text-sm font-medium">{{ selectedType ? `${selectedType.name} 字典项` : '字典项列表' }}</span>
                  <span class="text-xs text-gray-400">存储值保持原值，显示标签可配置中文</span>
                </div>
              </template>

              <el-empty v-if="!selectedType" description="请选择左侧字典类型" :image-size="64" />
              <template v-else>
                <el-table v-loading="itemLoading" :data="itemList" stripe class="w-full">
                  <el-table-column prop="value" label="存储值" min-width="180">
                    <template #default="{ row }">
                      <el-tag type="info" size="small">{{ row.value }}</el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column prop="label" label="显示标签" min-width="180" />
                  <el-table-column prop="sort_order" label="排序" width="90" align="center" />
                  <el-table-column label="状态" width="88" align="center">
                    <template #default="{ row }">
                      <el-tag :type="row.is_active ? 'success' : 'info'" size="small">{{ row.is_active ? '启用' : '禁用' }}</el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column prop="description" label="描述" min-width="220" show-overflow-tooltip />
                  <el-table-column label="操作" width="140" fixed="right">
                    <template #default="{ row }">
                      <el-button v-if="canWrite" link type="primary" @click="openItemDialog(row)">编辑</el-button>
                      <el-button v-if="canDelete" link type="danger" @click="deleteItem(row)">删除</el-button>
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
                    @change="loadItems"
                  />
                </div>
              </template>
            </el-card>
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="资源分类树" name="resource-categories">
        <div class="tab-pane-body flex gap-4 h-full">
          <el-card class="w-[380px] flex-shrink-0" shadow="never" body-style="padding:12px;display:flex;flex-direction:column;height:100%">
            <template #header>
              <div class="flex items-center justify-between gap-2">
                <span class="text-sm font-medium">分类树</span>
                <el-button v-if="canWrite" type="primary" link :icon="Plus" @click="openCategoryDialog('create-root')">新增根分类</el-button>
              </div>
            </template>

            <div class="mb-3 flex flex-col gap-2">
              <el-select v-model="resourceTypeFilter" class="w-full" @change="handleResourceTypeChange">
                <el-option v-for="item in resourceTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
              </el-select>
              <el-input
                v-model="resourceCategoryKeyword"
                placeholder="搜索分类名称 / 编码"
                :prefix-icon="Search"
                clearable
              />
            </div>

            <el-scrollbar max-height="calc(100vh - 280px)">
              <el-tree
                v-if="resourceCategoryTree.length > 0"
                :data="resourceCategoryTree"
                node-key="id"
                default-expand-all
                highlight-current
                :expand-on-click-node="false"
                :current-node-key="selectedResourceCategoryId ?? undefined"
                :props="{ children: 'children', label: 'name' }"
                class="category-tree"
                @node-click="handleResourceCategoryClick"
              >
                <template #default="{ data }">
                  <div class="flex w-full items-center justify-between gap-2 pr-1 text-sm">
                    <div class="min-w-0">
                      <div class="truncate font-medium text-slate-800">{{ data.name }}</div>
                      <div class="truncate text-xs uppercase text-slate-400">{{ data.code }}</div>
                    </div>
                    <el-tag :type="data.is_active ? 'success' : 'info'" size="small">{{ data.is_active ? '启用' : '禁用' }}</el-tag>
                  </div>
                </template>
              </el-tree>
              <el-empty v-else description="当前资源类型暂无分类" :image-size="56" />
            </el-scrollbar>
          </el-card>

          <div class="flex-1 flex min-w-0 flex-col gap-3">
            <el-card shadow="never" body-style="padding:12px 16px">
              <div class="flex items-center gap-3">
                <div class="rounded-xl bg-slate-50 px-3 py-2 text-sm text-slate-600">
                  系统管理统一维护材料、设备、人员、工艺分类树；主数据页与工艺挂载会直接复用这里的结构。
                </div>
                <div class="flex-1" />
                <el-button v-if="canWrite" :icon="FolderAdd" :disabled="!selectedResourceCategory" @click="openCategoryDialog('create-child', selectedResourceCategory ?? undefined)">新增子分类</el-button>
                <el-button v-if="canWrite && selectedResourceCategory" type="primary" :icon="EditPen" @click="openCategoryDialog('edit', selectedResourceCategory)">编辑</el-button>
                <el-button v-if="canDelete && selectedResourceCategory" type="danger" plain :icon="Delete" @click="deleteResourceCategory(selectedResourceCategory)">删除</el-button>
              </div>
            </el-card>

            <el-card shadow="never" class="flex-1" body-style="padding:16px;height:100%">
              <template #header>
                <div class="flex items-center justify-between gap-2">
                  <span class="text-sm font-medium">{{ selectedResourceCategory ? `${selectedResourceCategory.name} 分类详情` : '分类详情' }}</span>
                  <el-button link :icon="RefreshRight" @click="loadResourceCategories">刷新</el-button>
                </div>
              </template>

              <el-empty v-if="!selectedResourceCategory" description="请选择左侧分类节点" :image-size="72" />
              <template v-else>
                <el-descriptions :column="2" border>
                  <el-descriptions-item label="分类名称">{{ selectedResourceCategory.name }}</el-descriptions-item>
                  <el-descriptions-item label="分类编码">{{ selectedResourceCategory.code }}</el-descriptions-item>
                  <el-descriptions-item label="资源类型">{{ getResourceTypeLabel(selectedResourceCategory.resource_type) }}</el-descriptions-item>
                  <el-descriptions-item label="状态">
                    <el-tag :type="selectedResourceCategory.is_active ? 'success' : 'info'" size="small">
                      {{ selectedResourceCategory.is_active ? '启用' : '禁用' }}
                    </el-tag>
                  </el-descriptions-item>
                  <el-descriptions-item label="父分类">{{ selectedResourceCategoryParentName }}</el-descriptions-item>
                  <el-descriptions-item label="排序">{{ selectedResourceCategory.sort_order }}</el-descriptions-item>
                  <el-descriptions-item label="描述" :span="2">{{ selectedResourceCategory.description || '暂无描述' }}</el-descriptions-item>
                </el-descriptions>

                <div class="mt-5">
                  <div class="mb-3 flex items-center justify-between">
                    <span class="text-sm font-medium text-slate-700">直属子分类</span>
                    <span class="text-xs text-slate-400">有子分类或有业务数据绑定时，当前分类不可删除</span>
                  </div>
                  <el-table :data="selectedResourceCategoryChildren" size="small" stripe>
                    <el-table-column prop="name" label="名称" min-width="180" />
                    <el-table-column prop="code" label="编码" min-width="160" />
                    <el-table-column prop="sort_order" label="排序" width="90" align="center" />
                    <el-table-column label="状态" width="90" align="center">
                      <template #default="{ row }">
                        <el-tag :type="row.is_active ? 'success' : 'info'" size="small">{{ row.is_active ? '启用' : '禁用' }}</el-tag>
                      </template>
                    </el-table-column>
                  </el-table>
                </div>
              </template>
            </el-card>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>

    <DictTypeFormDialog v-model="typeDialogVisible" :data="currentType" @success="handleTypeSaved" />
    <DictItemFormDialog
      v-model="itemDialogVisible"
      :data="currentItem"
      :type-options="typeList"
      :default-type-id="selectedType?.id ?? null"
      @success="handleItemSaved"
    />

    <el-dialog
      v-model="resourceCategoryDialogVisible"
      :title="resourceCategoryDialogTitle"
      width="620px"
      :close-on-click-modal="false"
      @closed="resetResourceCategoryForm"
    >
      <el-form ref="resourceCategoryFormRef" :model="resourceCategoryForm" :rules="resourceCategoryRules" label-width="100px">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="分类名称" prop="name">
              <el-input v-model="resourceCategoryForm.name" maxlength="50" placeholder="请输入分类名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="分类编码" prop="code">
              <el-input v-model="resourceCategoryForm.code" maxlength="50" placeholder="纯大写英文，如 MATERIAL_RAW" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="资源类型" prop="resource_type">
              <el-select v-model="resourceCategoryForm.resource_type" class="w-full" :disabled="resourceCategoryDialogMode === 'edit'">
                <el-option v-for="item in resourceTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="父分类" prop="parent_id">
              <el-tree-select
                v-model="resourceCategoryForm.parent_id"
                :data="resourceCategoryParentTree"
                node-key="id"
                check-strictly
                filterable
                clearable
                :props="{ label: 'name', children: 'children' }"
                class="w-full"
                placeholder="根分类可留空"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="排序" prop="sort_order">
              <el-input-number v-model="resourceCategoryForm.sort_order" :min="0" controls-position="right" class="w-full" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="启用状态" prop="is_active">
              <el-switch v-model="resourceCategoryForm.is_active" active-text="启用" inactive-text="禁用" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="分类描述" prop="description">
          <el-input v-model="resourceCategoryForm.description" type="textarea" :rows="3" maxlength="256" show-word-limit placeholder="请输入分类说明" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="resourceCategoryDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="resourceCategorySaving" @click="submitResourceCategory">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { Delete, EditPen, FolderAdd, Plus, RefreshRight, Search } from '@element-plus/icons-vue'
import { ResourceType, systemDictionaryApi } from '@/api/systemDictionary'
import type {
  DictionaryItem,
  DictionaryType,
  ResourceCategory,
  ResourceCategoryCreate,
  ResourceType as ResourceCategoryType,
} from '@/api/systemDictionary'
import DictItemFormDialog from '@/components/system/DictItemFormDialog.vue'
import DictTypeFormDialog from '@/components/system/DictTypeFormDialog.vue'
import { useDictionaryStore } from '@/stores/dictionaries'
import { useAuthStore } from '@/stores/auth'

type CategoryTreeNode = ResourceCategory & { children: CategoryTreeNode[] }
type ResourceCategoryDialogMode = 'create-root' | 'create-child' | 'edit'

const authStore = useAuthStore()
const dictionaryStore = useDictionaryStore()
const canWrite = computed(() => authStore.hasPermissionScope('/system/dictionaries:write'))
const canDelete = computed(() => authStore.hasPermissionScope('/system/dictionaries:delete'))

const activeTab = ref<'system' | 'resource-categories'>('system')

const typeList = ref<DictionaryType[]>([])
const selectedType = ref<DictionaryType | null>(null)
const typeKeyword = ref('')
const typeDialogVisible = ref(false)
const currentType = ref<DictionaryType | null>(null)

const itemList = ref<DictionaryItem[]>([])
const itemLoading = ref(false)
const itemKeyword = ref('')
const itemActive = ref<boolean | null>(null)
const itemDialogVisible = ref(false)
const currentItem = ref<DictionaryItem | null>(null)
const pagination = reactive({ page: 1, size: 20, total: 0 })

const resourceTypeOptions: Array<{ label: string; value: ResourceCategoryType }> = [
  { label: '材料', value: ResourceType.MATERIAL },
  { label: '设备', value: ResourceType.EQUIPMENT },
  { label: '人员', value: ResourceType.LABOR },
  { label: '工艺', value: ResourceType.PROCESS },
  { label: '工具', value: ResourceType.TOOL },
]

const resourceTypeLabelMap = new Map(resourceTypeOptions.map((item) => [item.value, item.label]))
const resourceTypeFilter = ref<ResourceCategoryType>(ResourceType.MATERIAL)
const resourceCategoryList = ref<ResourceCategory[]>([])
const resourceCategoryKeyword = ref('')
const selectedResourceCategoryId = ref<number | null>(null)
const resourceCategoryDialogVisible = ref(false)
const resourceCategoryDialogMode = ref<ResourceCategoryDialogMode>('create-root')
const resourceCategorySaving = ref(false)
const resourceCategoryFormRef = ref<FormInstance>()
const resourceCategoryEditingId = ref<number | null>(null)
const resourceCategoryForm = reactive<ResourceCategoryCreate>({
  name: '',
  code: '',
  resource_type: ResourceType.MATERIAL,
  parent_id: null,
  sort_order: 0,
  is_active: true,
  description: null,
})
const resourceCategoryRules: FormRules = {
  name: [{ required: true, message: '请输入分类名称', trigger: 'blur' }],
  code: [
    { required: true, message: '请输入分类编码', trigger: 'blur' },
    { pattern: /^[A-Z][A-Z0-9_]*$/, message: '编码需为纯大写英文/数字/下划线', trigger: 'blur' },
  ],
  resource_type: [{ required: true, message: '请选择资源类型', trigger: 'change' }],
}

const selectedResourceCategory = computed(() =>
  resourceCategoryList.value.find((item) => item.id === selectedResourceCategoryId.value) ?? null,
)

const selectedResourceCategoryChildren = computed(() =>
  resourceCategoryList.value.filter((item) => item.parent_id === selectedResourceCategoryId.value),
)

const selectedResourceCategoryParentName = computed(() => {
  const parentId = selectedResourceCategory.value?.parent_id
  if (!parentId) {
    return '根分类'
  }
  return resourceCategoryList.value.find((item) => item.id === parentId)?.name ?? '未知父分类'
})

const resourceCategoryDialogTitle = computed(() => {
  if (resourceCategoryDialogMode.value === 'edit') {
    return '编辑资源分类'
  }
  return resourceCategoryDialogMode.value === 'create-child' ? '新增子分类' : '新增根分类'
})

const resourceCategoryTree = computed(() => {
  const tree = buildCategoryTree(resourceCategoryList.value)
  if (!resourceCategoryKeyword.value.trim()) {
    return tree
  }
  return filterCategoryTree(tree, resourceCategoryKeyword.value.trim().toLowerCase())
})

const resourceCategoryParentTree = computed(() => {
  const filtered = resourceCategoryList.value.filter((item) => item.id !== resourceCategoryEditingId.value)
  return buildCategoryTree(filtered)
})

function buildCategoryTree(items: ResourceCategory[]): CategoryTreeNode[] {
  const map = new Map<number, CategoryTreeNode>()
  const roots: CategoryTreeNode[] = []

  items.forEach((item) => {
    map.set(item.id, { ...item, children: [] })
  })

  items.forEach((item) => {
    const node = map.get(item.id)
    if (!node) {
      return
    }
    if (item.parent_id && map.has(item.parent_id)) {
      map.get(item.parent_id)?.children.push(node)
    } else {
      roots.push(node)
    }
  })

  const sortNodes = (nodes: CategoryTreeNode[]) => {
    nodes.sort((left, right) => (left.sort_order - right.sort_order) || (left.id - right.id))
    nodes.forEach((node) => sortNodes(node.children))
  }
  sortNodes(roots)

  return roots
}

function filterCategoryTree(nodes: CategoryTreeNode[], keyword: string): CategoryTreeNode[] {
  return nodes
    .map((node) => ({
      ...node,
      children: filterCategoryTree(node.children, keyword),
    }))
    .filter((node) => {
      const selfMatched = node.name.toLowerCase().includes(keyword) || node.code.toLowerCase().includes(keyword)
      return selfMatched || node.children.length > 0
    })
}

function getResourceTypeLabel(type: ResourceCategoryType) {
  return resourceTypeLabelMap.get(type) ?? type
}

function getErrorMessage(error: unknown, fallback: string) {
  const maybe = error as { response?: { data?: { message?: string; detail?: string } } }
  return maybe.response?.data?.message || maybe.response?.data?.detail || fallback
}

async function loadTypes() {
  const response = await systemDictionaryApi.listTypes({
    keyword: typeKeyword.value || undefined,
    page: 1,
    size: 200,
  })
  typeList.value = response.data.items
  if (!selectedType.value) {
    selectedType.value = typeList.value[0] ?? null
  } else {
    selectedType.value = typeList.value.find((item) => item.id === selectedType.value?.id) ?? typeList.value[0] ?? null
  }
  await loadItems()
}

function selectType(item: DictionaryType) {
  selectedType.value = item
  pagination.page = 1
  void loadItems()
}

function handleItemFilter() {
  pagination.page = 1
  void loadItems()
}

async function loadItems() {
  if (!selectedType.value) {
    itemList.value = []
    pagination.total = 0
    return
  }

  itemLoading.value = true
  try {
    const response = await systemDictionaryApi.listItems({
      dict_type_id: selectedType.value.id,
      keyword: itemKeyword.value || undefined,
      is_active: itemActive.value ?? undefined,
      page: pagination.page,
      size: pagination.size,
    })
    itemList.value = response.data.items
    pagination.total = response.data.total
  } finally {
    itemLoading.value = false
  }
}

function openTypeDialog(item?: DictionaryType) {
  currentType.value = item ?? null
  typeDialogVisible.value = true
}

function openItemDialog(item?: DictionaryItem) {
  currentItem.value = item ?? null
  itemDialogVisible.value = true
}

async function deleteType(item: DictionaryType) {
  try {
    await ElMessageBox.confirm(`确定删除字典类型「${item.name}」吗？`, '警告', { type: 'warning' })
    await systemDictionaryApi.removeType(item.id)
    ElMessage.success('已删除')
    await loadTypes()
    await dictionaryStore.ensureLoaded(true)
  } catch (error: unknown) {
    if (error === 'cancel' || error === 'close') {
      return
    }
  }
}

async function deleteItem(item: DictionaryItem) {
  try {
    await ElMessageBox.confirm(`确定删除字典项「${item.label}（${item.value}）」吗？`, '警告', { type: 'warning' })
    await systemDictionaryApi.removeItem(item.id)
    ElMessage.success('已删除')
    await loadItems()
    await dictionaryStore.ensureLoaded(true)
  } catch (error: unknown) {
    if (error === 'cancel' || error === 'close') {
      return
    }
  }
}

async function handleTypeSaved() {
  await loadTypes()
  await dictionaryStore.ensureLoaded(true)
}

async function handleItemSaved() {
  await loadItems()
  await dictionaryStore.ensureLoaded(true)
}

async function loadResourceCategories() {
  const response = await systemDictionaryApi.listResourceCategories({
    resource_type: resourceTypeFilter.value,
    page: 1,
    size: 1000,
  })
  resourceCategoryList.value = response.data.items
  if (
    selectedResourceCategoryId.value !== null
    && !resourceCategoryList.value.some((item) => item.id === selectedResourceCategoryId.value)
  ) {
    selectedResourceCategoryId.value = null
  }
  if (selectedResourceCategoryId.value === null) {
    selectedResourceCategoryId.value = resourceCategoryList.value[0]?.id ?? null
  }
}

function handleResourceTypeChange() {
  resourceCategoryKeyword.value = ''
  selectedResourceCategoryId.value = null
  void loadResourceCategories()
}

function handleResourceCategoryClick(node: CategoryTreeNode) {
  selectedResourceCategoryId.value = node.id
}

function resetResourceCategoryForm() {
  resourceCategoryFormRef.value?.resetFields()
  resourceCategoryEditingId.value = null
  resourceCategoryForm.name = ''
  resourceCategoryForm.code = ''
  resourceCategoryForm.resource_type = resourceTypeFilter.value
  resourceCategoryForm.parent_id = null
  resourceCategoryForm.sort_order = 0
  resourceCategoryForm.is_active = true
  resourceCategoryForm.description = null
}

function openCategoryDialog(mode: ResourceCategoryDialogMode, item?: ResourceCategory) {
  resourceCategoryDialogMode.value = mode
  resetResourceCategoryForm()

  if (mode === 'create-root') {
    resourceCategoryForm.resource_type = resourceTypeFilter.value
  } else if (mode === 'create-child' && item) {
    resourceCategoryForm.resource_type = item.resource_type
    resourceCategoryForm.parent_id = item.id
  } else if (mode === 'edit' && item) {
    resourceCategoryEditingId.value = item.id
    resourceCategoryForm.name = item.name
    resourceCategoryForm.code = item.code
    resourceCategoryForm.resource_type = item.resource_type
    resourceCategoryForm.parent_id = item.parent_id
    resourceCategoryForm.sort_order = item.sort_order
    resourceCategoryForm.is_active = item.is_active
    resourceCategoryForm.description = item.description
  }

  resourceCategoryDialogVisible.value = true
}

async function submitResourceCategory() {
  const valid = await resourceCategoryFormRef.value?.validate().catch(() => false)
  if (!valid) {
    return
  }

  resourceCategorySaving.value = true
  try {
    if (resourceCategoryDialogMode.value === 'edit' && resourceCategoryEditingId.value) {
      const response = await systemDictionaryApi.updateResourceCategory(resourceCategoryEditingId.value, resourceCategoryForm)
      selectedResourceCategoryId.value = response.data.id
      ElMessage.success('分类已更新')
    } else {
      const response = await systemDictionaryApi.createResourceCategory(resourceCategoryForm)
      selectedResourceCategoryId.value = response.data.id
      ElMessage.success('分类已创建')
    }
    resourceCategoryDialogVisible.value = false
    await loadResourceCategories()
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '分类保存失败，请稍后重试'))
  } finally {
    resourceCategorySaving.value = false
  }
}

async function deleteResourceCategory(item: ResourceCategory) {
  try {
    await ElMessageBox.confirm(`确定删除分类「${item.name}」吗？`, '警告', { type: 'warning' })
    await systemDictionaryApi.removeResourceCategory(item.id)
    ElMessage.success('分类已删除')
    if (selectedResourceCategoryId.value === item.id) {
      selectedResourceCategoryId.value = null
    }
    await loadResourceCategories()
  } catch (error: unknown) {
    if (error === 'cancel' || error === 'close') {
      return
    }
    ElMessage.error(getErrorMessage(error, '分类删除失败，请稍后重试'))
  }
}

onMounted(() => {
  void Promise.all([loadTypes(), loadResourceCategories()])
})
</script>

<style scoped>
.dictionaries-tabs :deep(.el-tabs__content) {
  height: calc(100% - 55px);
}

.tab-pane-body {
  min-height: 0;
}

.category-tree :deep(.el-tree-node__content) {
  height: 40px;
  border-radius: 10px;
}

.category-tree :deep(.el-tree-node__content:hover) {
  background: #f8fafc;
}

.category-tree :deep(.el-tree--highlight-current .el-tree-node.is-current > .el-tree-node__content) {
  background: #eef2ff;
  color: #4338ca;
}
</style>