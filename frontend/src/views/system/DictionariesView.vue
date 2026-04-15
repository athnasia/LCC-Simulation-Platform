<template>
  <div class="flex gap-4 h-full">
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

    <DictTypeFormDialog v-model="typeDialogVisible" :data="currentType" @success="handleTypeSaved" />
    <DictItemFormDialog
      v-model="itemDialogVisible"
      :data="currentItem"
      :type-options="typeList"
      :default-type-id="selectedType?.id ?? null"
      @success="handleItemSaved"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import { systemDictionaryApi } from '@/api/systemDictionary'
import type { DictionaryItem, DictionaryType } from '@/api/systemDictionary'
import DictItemFormDialog from '@/components/system/DictItemFormDialog.vue'
import DictTypeFormDialog from '@/components/system/DictTypeFormDialog.vue'
import { useDictionaryStore } from '@/stores/dictionaries'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const dictionaryStore = useDictionaryStore()
const canWrite = computed(() => authStore.hasPermissionScope('/system/dictionaries:write'))
const canDelete = computed(() => authStore.hasPermissionScope('/system/dictionaries:delete'))

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

onMounted(() => {
  void loadTypes()
})
</script>