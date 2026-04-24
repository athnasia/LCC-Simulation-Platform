<template>
  <div class="h-full">
    <el-tabs v-model="activeTab" class="dictionaries-tabs h-full">
      <el-tab-pane label="系统字典" name="system">
        <div class="tab-pane-body flex gap-4 h-full">
          <aside class="dict-type-nav">
            <div class="dict-type-nav-header">
              <span class="text-sm font-medium">字典类型</span>
              <el-button v-if="canWrite" type="primary" link :icon="Plus" @click="openTypeDialog()">新建类型</el-button>
            </div>

            <div class="dict-type-nav-search">
              <el-input
                v-model="typeKeyword"
                placeholder="搜索名称 / 编码"
                :prefix-icon="Search"
                clearable
                @change="loadTypes"
              />
            </div>

            <el-scrollbar class="dict-type-scrollbar">
              <ul v-if="typeList.length > 0" class="dict-type-list">
                <li
                  v-for="item in typeList"
                  :key="item.id"
                  class="dict-type-item"
                  :class="{ 'is-active': selectedType?.id === item.id }"
                >
                  <div
                    class="dict-type-item-button"
                    role="button"
                    tabindex="0"
                    @click="selectType(item)"
                    @keydown.enter.prevent="selectType(item)"
                    @keydown.space.prevent="selectType(item)"
                  >
                    <div class="dict-type-item-main">
                      <div class="dict-type-item-title">{{ item.name }}</div>
                      <div class="dict-type-item-code">{{ item.code }}</div>
                    </div>
                    <div v-if="canWrite || canDelete" class="dict-type-item-actions">
                      <el-button
                        v-if="canWrite"
                        link
                        :icon="Edit"
                        class="dict-type-item-action"
                        aria-label="编辑字典类型"
                        @click.stop="openTypeDialog(item)"
                      />
                      <el-button
                        v-if="canDelete"
                        link
                        type="danger"
                        :icon="Delete"
                        class="dict-type-item-action"
                        aria-label="删除字典类型"
                        @click.stop="deleteType(item)"
                      />
                    </div>
                  </div>
                </li>
              </ul>
              <el-empty v-else description="暂无字典类型" :image-size="56" />
            </el-scrollbar>
          </aside>

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
                      <el-tag v-if="isCodeLikeValue(row.value)" type="info" size="small">{{ row.value }}</el-tag>
                      <span v-else>{{ row.value }}</span>
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
                  <el-table-column label="操作" width="110" fixed="right">
                    <template #default="{ row }">
                      <div class="flex items-center justify-center gap-1">
                        <el-button v-if="canWrite" link type="primary" :icon="Edit" aria-label="编辑字典项" @click="openItemDialog(row)" />
                        <el-button v-if="canDelete" link type="danger" :icon="Delete" aria-label="删除字典项" @click="deleteItem(row)" />
                      </div>
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
          <el-card class="w-[420px] flex-shrink-0" shadow="never" body-style="padding:12px;display:flex;flex-direction:column;height:100%">
            <template #header>
              <div class="flex items-center justify-between gap-2">
                <span class="text-sm font-medium">资源分类</span>
                <el-button v-if="canWrite" type="primary" link :icon="Plus" @click="openCategoryDialog()">新增分类</el-button>
              </div>
            </template>

            <div class="mb-3 flex flex-col gap-2">
              <el-input
                v-model="resourceCategoryKeyword"
                placeholder="搜索分类名称 / 编码"
                :prefix-icon="Search"
                clearable
              />
            </div>

            <el-scrollbar max-height="calc(100vh - 300px)">
              <el-tree
                v-if="resourceCategoryTree.length > 0"
                :data="resourceCategoryTree"
                node-key="key"
                default-expand-all
                highlight-current
                :expand-on-click-node="false"
                :current-node-key="selectedResourceTreeKey"
                :props="{ children: 'children', label: 'name' }"
                class="category-tree"
                @node-click="handleResourceCategoryClick"
              >
                <template #default="{ node, data }">
                  <div class="resource-tree-node" :title="node.label">
                    <el-icon class="resource-tree-node-icon">
                      <FolderOpened v-if="data.nodeType === 'root' || data.nodeType === 'type'" />
                      <CollectionTag v-else />
                    </el-icon>
                    <span class="resource-tree-node-label">{{ data.name }}</span>
                  </div>
                </template>
              </el-tree>
              <el-empty v-else description="暂无资源分类" :image-size="56" />
            </el-scrollbar>
          </el-card>

          <div class="flex-1 flex min-w-0 flex-col gap-3">
            <el-card shadow="never" body-style="padding:12px 16px">
              <div class="flex items-center gap-3">
                <el-alert
                  type="info"
                  :closable="false"
                  show-icon
                  class="resource-category-tip"
                  title="资源分类统一维护在一个根目录下，类型节点仅做分组，实际只保留一级分类。"
                />
                <div class="flex-1" />
                <el-button v-if="canWrite" :icon="Plus" @click="openCategoryDialog()">新增分类</el-button>
                <el-button v-if="canWrite && selectedResourceCategory" type="primary" :icon="EditPen" @click="openCategoryDialog(selectedResourceCategory)">编辑</el-button>
                <el-button v-if="canDelete && selectedResourceCategory" type="danger" plain :icon="Delete" @click="deleteResourceCategory(selectedResourceCategory)">删除</el-button>
              </div>
            </el-card>

            <el-card shadow="never" class="flex-1" body-style="padding:16px;height:100%">
              <template #header>
                <div class="flex items-center justify-between gap-2">
                  <span class="text-sm font-medium">{{ selectedResourceCategory ? `${selectedResourceCategory.name} 分类详情` : selectedResourceTypeLabel ? `${selectedResourceTypeLabel} 分类列表` : '资源分类' }}</span>
                  <el-button link :icon="RefreshRight" aria-label="刷新资源分类" @click="loadResourceCategories" />
                </div>
              </template>

              <template v-if="selectedResourceCategory">
                <el-descriptions :column="2" border>
                  <el-descriptions-item label="分类名称">{{ selectedResourceCategory.name }}</el-descriptions-item>
                  <el-descriptions-item label="分类编码">{{ selectedResourceCategory.code }}</el-descriptions-item>
                  <el-descriptions-item label="资源类型">{{ getResourceTypeLabel(selectedResourceCategory.resource_type) }}</el-descriptions-item>
                  <el-descriptions-item label="状态">
                    <el-tag :type="selectedResourceCategory.is_active ? 'success' : 'info'" size="small">
                      {{ selectedResourceCategory.is_active ? '启用' : '禁用' }}
                    </el-tag>
                  </el-descriptions-item>
                  <el-descriptions-item label="所属根目录">资源分类 / {{ getResourceTypeLabel(selectedResourceCategory.resource_type) }}</el-descriptions-item>
                  <el-descriptions-item label="排序">{{ selectedResourceCategory.sort_order }}</el-descriptions-item>
                  <el-descriptions-item label="描述" :span="2">{{ selectedResourceCategory.description || '暂无描述' }}</el-descriptions-item>
                </el-descriptions>
              </template>

              <template v-else-if="selectedResourceTypeLabel">
                <el-table :data="selectedTypeCategories" size="small" stripe>
                  <el-table-column prop="name" label="名称" min-width="180" />
                  <el-table-column prop="code" label="编码" min-width="180" />
                  <el-table-column prop="sort_order" label="排序" width="90" align="center" />
                  <el-table-column label="状态" width="90" align="center">
                    <template #default="{ row }">
                      <el-tag :type="row.is_active ? 'success' : 'info'" size="small">{{ row.is_active ? '启用' : '禁用' }}</el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column prop="description" label="描述" min-width="220" show-overflow-tooltip />
                </el-table>
              </template>

              <el-empty v-else description="请选择左侧类型或分类节点" :image-size="72" />
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
              <el-select v-model="resourceCategoryForm.resource_type" class="w-full">
                <el-option v-for="item in resourceTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="层级说明">
              <el-input value="固定挂在资源分类 / 类型节点下" readonly />
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
import { CollectionTag, Delete, Edit, EditPen, FolderOpened, Plus, RefreshRight, Search } from '@element-plus/icons-vue'
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

type ResourceTreeNode = {
  key: string
  name: string
  code?: string
  nodeType: 'root' | 'type' | 'category'
  resource_type?: ResourceCategoryType
  categoryId?: number
  count?: number
  is_active?: boolean
  children: ResourceTreeNode[]
}

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
const defaultResourceType = ResourceType.MATERIAL

const resourceTypeOptions: Array<{ label: string; value: ResourceCategoryType }> = [
  { label: '材料', value: ResourceType.MATERIAL },
  { label: '设备', value: ResourceType.EQUIPMENT },
  { label: '人员', value: ResourceType.LABOR },
  { label: '工艺', value: ResourceType.PROCESS },
]

const resourceTypeLabelMap = new Map(resourceTypeOptions.map((item) => [item.value, item.label]))
const resourceCategoryList = ref<ResourceCategory[]>([])
const resourceCategoryKeyword = ref('')
const selectedResourceTreeKey = ref('resource-root')
const selectedResourceCategoryId = ref<number | null>(null)
const selectedResourceType = ref<ResourceCategoryType | null>(defaultResourceType)
const resourceCategoryDialogVisible = ref(false)
const resourceCategorySaving = ref(false)
const resourceCategoryFormRef = ref<FormInstance>()
const resourceCategoryEditingId = ref<number | null>(null)
const resourceCategoryForm = reactive<ResourceCategoryCreate>({
  name: '',
  code: '',
  resource_type: defaultResourceType,
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

const selectedResourceTypeLabel = computed(() =>
  selectedResourceType.value ? getResourceTypeLabel(selectedResourceType.value) : '',
)

const selectedTypeCategories = computed(() => {
  if (!selectedResourceType.value) {
    return []
  }
  return [...resourceCategoryList.value]
    .filter((item) => item.resource_type === selectedResourceType.value)
    .sort((left, right) => (left.sort_order - right.sort_order) || (left.id - right.id))
})

const resourceCategoryDialogTitle = computed(() =>
  resourceCategoryEditingId.value ? '编辑资源分类' : '新增资源分类',
)

const resourceCategoryTree = computed(() => {
  return buildResourceCategoryTree(resourceCategoryList.value, resourceCategoryKeyword.value)
})

const codeLikeValuePattern = /^[A-Z][A-Z0-9_:-]*$/

function getTypeNodeKey(type: ResourceCategoryType) {
  return `resource-type-${type}`
}

function getCategoryNodeKey(id: number) {
  return `resource-category-${id}`
}

function buildResourceCategoryTree(items: ResourceCategory[], keyword: string): ResourceTreeNode[] {
  const normalizedKeyword = keyword.trim().toLowerCase()
  const typeNodes = resourceTypeOptions
    .map<ResourceTreeNode | null>((option) => {
      const categories = items
        .filter((item) => item.resource_type === option.value)
        .sort((left, right) => (left.sort_order - right.sort_order) || (left.id - right.id))

      const filteredCategories = categories.filter((item) => {
        if (!normalizedKeyword) {
          return true
        }
        return item.name.toLowerCase().includes(normalizedKeyword) || item.code.toLowerCase().includes(normalizedKeyword)
      })

      const typeMatched = !normalizedKeyword || option.label.toLowerCase().includes(normalizedKeyword)
      if (!typeMatched && filteredCategories.length === 0) {
        return null
      }

      return {
        key: getTypeNodeKey(option.value),
        name: option.label,
        nodeType: 'type',
        resource_type: option.value,
        count: categories.length,
        children: filteredCategories.map((item) => ({
          key: getCategoryNodeKey(item.id),
          name: item.name,
          code: item.code,
          nodeType: 'category',
          resource_type: item.resource_type,
          categoryId: item.id,
          is_active: item.is_active,
          children: [],
        })),
      }
    })
    .filter((node): node is ResourceTreeNode => node !== null)

  if (normalizedKeyword && typeNodes.length === 0 && !'资源分类'.includes(normalizedKeyword)) {
    return []
  }

  return [{
    key: 'resource-root',
    name: '资源分类',
    nodeType: 'root',
    children: typeNodes,
  }]
}

function getResourceTypeLabel(type: ResourceCategoryType) {
  return resourceTypeLabelMap.get(type) ?? type
}

function isCodeLikeValue(value: string) {
  return codeLikeValuePattern.test(value)
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
  const response = await systemDictionaryApi.listResourceCategories({ page: 1, size: 1000 })
  resourceCategoryList.value = response.data.items

  if (selectedResourceCategoryId.value !== null && !resourceCategoryList.value.some((item) => item.id === selectedResourceCategoryId.value)) {
    selectedResourceCategoryId.value = null
  }

  if (selectedResourceCategoryId.value !== null) {
    selectedResourceTreeKey.value = getCategoryNodeKey(selectedResourceCategoryId.value)
    selectedResourceType.value = selectedResourceCategory.value?.resource_type ?? selectedResourceType.value
    return
  }

  if (selectedResourceType.value && resourceTypeOptions.some((item) => item.value === selectedResourceType.value)) {
    selectedResourceTreeKey.value = getTypeNodeKey(selectedResourceType.value)
    return
  }

  selectedResourceType.value = resourceTypeOptions[0]?.value ?? null
  selectedResourceTreeKey.value = selectedResourceType.value ? getTypeNodeKey(selectedResourceType.value) : 'resource-root'
}

function handleResourceCategoryClick(node: ResourceTreeNode) {
  selectedResourceTreeKey.value = node.key

  if (node.nodeType === 'category') {
    selectedResourceCategoryId.value = node.categoryId ?? null
    selectedResourceType.value = node.resource_type ?? null
    return
  }

  selectedResourceCategoryId.value = null
  selectedResourceType.value = node.nodeType === 'type' ? (node.resource_type ?? null) : null
}

function resetResourceCategoryForm() {
  resourceCategoryFormRef.value?.resetFields()
  resourceCategoryEditingId.value = null
  resourceCategoryForm.name = ''
  resourceCategoryForm.code = ''
  resourceCategoryForm.resource_type = selectedResourceType.value ?? defaultResourceType
  resourceCategoryForm.parent_id = null
  resourceCategoryForm.sort_order = 0
  resourceCategoryForm.is_active = true
  resourceCategoryForm.description = null
}

function openCategoryDialog(item?: ResourceCategory) {
  resetResourceCategoryForm()

  if (item) {
    resourceCategoryEditingId.value = item.id
    resourceCategoryForm.name = item.name
    resourceCategoryForm.code = item.code
    resourceCategoryForm.resource_type = item.resource_type
    resourceCategoryForm.parent_id = null
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
    const payload = {
      ...resourceCategoryForm,
      parent_id: null,
    }

    if (resourceCategoryEditingId.value) {
      const response = await systemDictionaryApi.updateResourceCategory(resourceCategoryEditingId.value, payload)
      selectedResourceCategoryId.value = response.data.id
      selectedResourceType.value = response.data.resource_type
      selectedResourceTreeKey.value = getCategoryNodeKey(response.data.id)
      ElMessage.success('分类已更新')
    } else {
      const response = await systemDictionaryApi.createResourceCategory(payload)
      selectedResourceCategoryId.value = response.data.id
      selectedResourceType.value = response.data.resource_type
      selectedResourceTreeKey.value = getCategoryNodeKey(response.data.id)
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
      selectedResourceType.value = item.resource_type
      selectedResourceTreeKey.value = getTypeNodeKey(item.resource_type)
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

.dict-type-nav {
  width: 320px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  min-height: 0;
  padding-right: 8px;
  border-right: 1px solid var(--el-border-color-lighter);
}

.dict-type-nav-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 4px 0 12px;
}

.dict-type-nav-search {
  padding: 0 0 12px;
}

.dict-type-scrollbar {
  flex: 1;
  min-height: 0;
}

.dict-type-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding-right: 6px;
}

.dict-type-item {
  list-style: none;
  border-left: 3px solid transparent;
  border-radius: 0 12px 12px 0;
  transition: background-color 0.2s ease, border-color 0.2s ease;
}

.dict-type-item:hover,
.dict-type-item:focus-within {
  background: var(--el-fill-color-light);
}

.dict-type-item.is-active {
  background: var(--el-color-primary-light-9);
  border-left-color: var(--el-color-primary);
}

.dict-type-item.is-active:hover,
.dict-type-item.is-active:focus-within {
  background: var(--el-color-primary-light-9);
}

.dict-type-item-button {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 10px 12px 14px;
  background: transparent;
  border: 0;
  text-align: left;
  cursor: pointer;
}

.dict-type-item-main {
  min-width: 0;
  flex: 1;
}

.dict-type-item-title {
  overflow: hidden;
  font-size: 14px;
  font-weight: 600;
  line-height: 20px;
  color: var(--el-text-color-primary);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dict-type-item-code {
  overflow: hidden;
  margin-top: 2px;
  font-size: 12px;
  line-height: 18px;
  color: var(--el-text-color-secondary);
  letter-spacing: 0.04em;
  text-overflow: ellipsis;
  text-transform: uppercase;
  white-space: nowrap;
}

.dict-type-item-actions {
  display: flex;
  align-items: center;
  gap: 2px;
  opacity: 0;
  transform: translateX(4px);
  pointer-events: none;
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.dict-type-item:hover .dict-type-item-actions,
.dict-type-item:focus-within .dict-type-item-actions,
.dict-type-item.is-active .dict-type-item-actions {
  opacity: 1;
  transform: translateX(0);
  pointer-events: auto;
}

.dict-type-item-action {
  min-width: 28px;
  height: 28px;
  padding: 0;
}

.resource-category-tip {
  flex: 1;
  min-width: 0;
  margin: 0;
}

.resource-category-tip :deep(.el-alert) {
  padding: 8px 12px;
  border: 0;
  background: var(--el-color-info-light-9);
}

.resource-category-tip :deep(.el-alert__icon) {
  margin-right: 8px;
  font-size: 14px;
}

.resource-category-tip :deep(.el-alert__title) {
  font-size: 12px;
  line-height: 18px;
  color: var(--el-text-color-regular);
}

.resource-tree-node {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  min-width: 0;
}

.resource-tree-node-icon {
  flex-shrink: 0;
  font-size: 14px;
  color: var(--el-color-primary);
}

.resource-tree-node-label {
  overflow: hidden;
  font-size: 13px;
  line-height: 20px;
  color: var(--el-text-color-primary);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.category-tree :deep(.el-tree-node__content) {
  height: 36px;
  border-radius: 10px;
  padding-right: 10px;
}

.category-tree :deep(.el-tree-node__content:hover) {
  background: #f8fafc;
}

.category-tree :deep(.el-tree--highlight-current .el-tree-node.is-current > .el-tree-node__content) {
  background: #eef2ff;
  color: #4338ca;
}
</style>