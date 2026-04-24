<template>
  <div class="dictionary-page flex h-full min-h-0 flex-col gap-4 p-6">
    <div class="page-header flex flex-col gap-3 rounded-2xl border border-slate-200 bg-white/90 px-4 py-3 shadow-sm lg:flex-row lg:items-center lg:justify-between">
      <div class="min-w-0">
        <p class="text-[11px] font-semibold uppercase tracking-[0.28em] text-sky-600">Module 02</p>
        <h2 class="mt-1 text-2xl font-semibold text-slate-900">基础字典与模板</h2>
        <p class="mt-1 max-w-3xl text-sm leading-6 text-slate-500">
          统一维护量纲、单位与柔性属性模板，确保材料台账、设备能力库与成本公式引擎使用同一套主数据底座。
        </p>
      </div>
      <div class="header-stats flex items-center gap-2 rounded-xl border border-slate-200/80 bg-slate-50/90 px-3 py-2 text-sm text-slate-600 lg:flex-nowrap">
        <div class="header-stat-item">
          <span class="stat-label">量纲数</span>
          <span class="stat-value">{{ summaryStats.dimensions }}</span>
        </div>
        <el-divider direction="vertical" />
        <div class="header-stat-item">
          <span class="stat-label">单位数</span>
          <span class="stat-value">{{ summaryStats.units }}</span>
        </div>
        <el-divider direction="vertical" />
        <div class="header-stat-item">
          <span class="stat-label">属性数</span>
          <span class="stat-value">{{ summaryStats.attributes }}</span>
        </div>
      </div>
    </div>

    <el-tabs v-model="activeTab" class="flex-1 min-h-0">
      <el-tab-pane label="计量单位管理" name="units" class="h-full">
        <div class="grid h-full min-h-0 gap-4 xl:grid-cols-[280px_minmax(0,1fr)]">
          <div class="dimension-sidebar flex min-h-0 flex-col rounded-2xl border border-slate-200/80 bg-white/80 p-3 shadow-sm">
            <el-button
              v-if="canWrite"
              plain
              :icon="Plus"
              class="dimension-create-button mb-3 w-full"
              @click="openDimensionDialog()"
            >
              新建量纲
            </el-button>

            <div class="mb-3 flex items-center gap-2">
              <el-input
                v-model="dimensionKeyword"
                clearable
                placeholder="搜索量纲名称 / 编码"
                :prefix-icon="Search"
                @keyup.enter="loadDimensions(false)"
                @clear="loadDimensions(false)"
              />
              <el-button :icon="RefreshRight" @click="loadDimensions(false)" />
            </div>

            <div v-loading="dimensionLoading" class="min-h-0 flex-1 overflow-hidden">
              <el-scrollbar max-height="calc(100vh - 308px)">
                <ul v-if="dimensionList.length > 0" class="dimension-menu pr-1">
                  <li v-for="dimension in dimensionList" :key="dimension.id">
                    <button
                      type="button"
                      class="dimension-menu__item"
                      :class="{ 'dimension-menu__item--active': selectedDimensionId === dimension.id }"
                      @click="selectDimension(dimension.id)"
                    >
                      <div class="min-w-0 flex-1 text-left">
                        <div class="truncate text-sm font-semibold text-slate-900">{{ dimension.name }}</div>
                        <div class="mt-0.5 truncate text-[11px] uppercase tracking-[0.22em] text-slate-400">
                          {{ dimension.code }}
                        </div>
                      </div>
                      <div class="dimension-menu__actions">
                        <button
                          v-if="canWrite"
                          type="button"
                          class="dimension-menu__icon dimension-menu__icon--edit"
                          @click.stop="openDimensionDialog(dimension)"
                        >
                          <el-icon><Edit /></el-icon>
                        </button>
                        <button
                          v-if="canDelete"
                          type="button"
                          class="dimension-menu__icon dimension-menu__icon--delete"
                          @click.stop="deleteDimension(dimension)"
                        >
                          <el-icon><Delete /></el-icon>
                        </button>
                      </div>
                    </button>
                  </li>
                </ul>
                <el-empty v-else :image-size="56" description="暂无量纲数据" />
              </el-scrollbar>
            </div>
          </div>

          <el-card shadow="never" class="min-h-0 border-slate-200" body-style="padding:0; display:flex; flex-direction:column; min-height:0;">
            <template #header>
              <div class="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                <div>
                  <div class="text-base font-semibold text-slate-900">
                    {{ selectedDimension ? `${selectedDimension.name} 单位台账` : '单位台账' }}
                  </div>
                  <div class="mt-1 text-xs text-slate-500">按量纲集中维护单位台账与换算关系。</div>
                </div>
                <div class="flex flex-wrap items-center gap-2">
                  <el-input
                    v-model="unitQuery.keyword"
                    class="w-64"
                    clearable
                    placeholder="搜索单位名称 / 编码"
                    :prefix-icon="Search"
                    @keyup.enter="handleUnitFilter"
                    @clear="handleUnitFilter"
                  />
                  <el-select v-model="unitQuery.unitType" class="w-36" @change="handleUnitFilter">
                    <el-option label="全部类型" value="ALL" />
                    <el-option
                      v-for="item in unitKindOptions"
                      :key="item.value"
                      :label="item.label"
                      :value="item.value"
                    />
                  </el-select>
                  <el-button v-if="canWrite" type="primary" :icon="Plus" :disabled="!selectedDimension" @click="openUnitDialog()">
                    新建单位
                  </el-button>
                </div>
              </div>
            </template>

            <div v-if="selectedDimension" class="flex min-h-0 flex-1 flex-col">
              <div class="px-4 pt-4">
                <el-alert
                  :type="baseUnit ? 'success' : 'warning'"
                  :closable="false"
                  show-icon
                >
                  <template #title>
                    <template v-if="baseUnit">
                      当前基准单位：{{ baseUnit.name }}（{{ baseUnit.symbol || baseUnit.code }}）
                    </template>
                    <template v-else>
                      当前量纲尚未配置基准单位，请优先创建基准单位。
                    </template>
                  </template>
                </el-alert>
              </div>

              <el-table
                v-loading="unitLoading"
                :data="unitList"
                stripe
                class="w-full flex-1"
                height="100%"
              >
                <el-table-column prop="name" label="名称" min-width="180" show-overflow-tooltip />
                <el-table-column prop="symbol" label="符号" width="100" align="center">
                  <template #default="{ row }">
                    <span>{{ row.symbol || row.code }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="类型" width="120" align="center">
                  <template #default="{ row }">
                    <el-tag :type="row.is_base ? 'success' : 'info'" size="small">
                      {{ getUnitKindLabel(row.is_base ? 'BASE' : 'CONVERTED') }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="转换系数" min-width="220">
                  <template #default="{ row }">
                    <template v-if="row.is_base">
                      <el-tag type="success" effect="dark" size="small">基准</el-tag>
                    </template>
                    <template v-else>
                      <div class="unit-formula-chip">
                        {{ formatUnitFormula(row) }}
                      </div>
                      <div class="mt-2 text-xs text-slate-500">
                        换算系数：{{ formatFactor(conversionFactorMap[row.id]) }}
                      </div>
                    </template>
                  </template>
                </el-table-column>
                <el-table-column prop="description" label="说明" min-width="220" show-overflow-tooltip />
                <el-table-column prop="updated_at" label="更新时间" width="168">
                  <template #default="{ row }">
                    {{ formatDate(row.updated_at) }}
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="140" fixed="right">
                  <template #default="{ row }">
                    <el-button v-if="canWrite" link type="primary" @click="openUnitDialog(row)">
                      编辑
                    </el-button>
                    <el-button v-if="canDelete" link type="danger" @click="deleteUnit(row)">
                      删除
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>

              <div class="flex justify-end border-t border-slate-100 px-4 py-4">
                <el-pagination
                  v-model:current-page="unitPagination.page"
                  v-model:page-size="unitPagination.size"
                  :page-sizes="[10, 20, 50]"
                  :total="unitPagination.total"
                  layout="total, sizes, prev, pager, next"
                  @change="loadUnitsAndConversions"
                />
              </div>
            </div>
            <div v-else class="flex flex-1 items-center justify-center py-12">
              <el-empty description="请选择左侧量纲后开始维护单位" />
            </div>
          </el-card>
        </div>
      </el-tab-pane>

      <el-tab-pane label="柔性属性模板" name="attributes" class="h-full">
        <el-card shadow="never" class="min-h-0 border-slate-200" body-style="padding:0; display:flex; flex-direction:column; min-height:0;">
          <template #header>
            <div>
              <div class="text-base font-semibold text-slate-900">柔性属性模板</div>
              <div class="mt-1 text-xs text-slate-500">
                为材料、设备等资源定义可扩展属性，供主数据录入和公式解析引擎统一复用。
              </div>
            </div>
          </template>

          <div class="flex min-h-0 flex-1 flex-col">
            <div class="flex flex-col gap-3 border-b border-slate-100 px-4 py-4 xl:flex-row xl:items-center xl:justify-between">
              <div class="flex flex-1 flex-wrap items-center gap-2">
                <el-input
                  v-model="attrQuery.keyword"
                  class="w-full xl:w-[280px]"
                  clearable
                  placeholder="搜索属性名称 / 编码"
                  :prefix-icon="Search"
                  @keyup.enter="handleAttrFilter"
                  @clear="handleAttrFilter"
                />
                <el-select v-model="attrQuery.dataType" clearable class="w-full xl:w-[180px]" placeholder="数据类型" @change="handleAttrFilter">
                  <el-option
                    v-for="item in attrDataTypeOptions"
                    :key="item.value"
                    :label="item.label"
                    :value="item.value"
                  />
                </el-select>
                <el-select v-model="attrQuery.resourceType" clearable class="w-full xl:w-[180px]" placeholder="资源类型" @change="handleAttrFilter">
                  <el-option
                    v-for="item in resourceTypeOptions"
                    :key="item.value"
                    :label="item.label"
                    :value="item.value"
                  />
                </el-select>
              </div>
              <div class="flex justify-end">
                <el-button v-if="canWrite" type="primary" :icon="Plus" @click="openAttrDialog()">
                  新建属性
                </el-button>
              </div>
            </div>

            <el-table
              v-loading="attrLoading"
              :data="attrList"
              stripe
              class="w-full flex-1"
              height="100%"
            >
              <el-table-column prop="code" label="属性编码" min-width="180" show-overflow-tooltip />
              <el-table-column prop="name" label="属性名称" min-width="180" show-overflow-tooltip />
              <el-table-column prop="data_type" label="数据类型" width="120" align="center">
                <template #default="{ row }">
                  <el-tag size="small" type="info" effect="plain">{{ getAttrDataTypeLabel(row.data_type) }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="关联单位" width="140">
                <template #default="{ row }">
                  <span v-if="row.unit">{{ row.unit.name }}（{{ row.unit.symbol || row.unit.code }}）</span>
                  <span v-else class="text-slate-400">-</span>
                </template>
              </el-table-column>
              <el-table-column label="适用资源类型" min-width="220">
                <template #default="{ row }">
                  <div class="flex flex-wrap gap-1">
                    <el-tag
                      v-if="isAttrApplicableToAll(row.applicable_resource_types)"
                      size="small"
                      type="warning"
                      effect="light"
                    >
                      适用全部
                    </el-tag>
                    <el-tag
                      v-for="type in getDisplayApplicableResourceTypes(row.applicable_resource_types)"
                      :key="type"
                      size="small"
                      :type="getAttrResourceTagType(type)"
                      effect="light"
                    >
                      {{ getResourceTypeLabel(type) }}
                    </el-tag>
                    <span v-if="row.applicable_resource_types.length === 0" class="text-slate-400">-</span>
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="默认值" min-width="140" show-overflow-tooltip>
                <template #default="{ row }">
                  <span>{{ row.default_value || '-' }}</span>
                </template>
              </el-table-column>
              <el-table-column label="必填" width="88" align="center">
                <template #default="{ row }">
                  <span v-if="row.is_required" class="text-sm font-semibold text-rose-600">必填</span>
                  <span v-else class="text-sm text-slate-400">否</span>
                </template>
              </el-table-column>
              <el-table-column prop="updated_at" label="更新时间" width="168">
                <template #default="{ row }">
                  {{ formatDate(row.updated_at) }}
                </template>
              </el-table-column>
              <el-table-column label="操作" width="92" fixed="right" align="center">
                <template #default="{ row }">
                  <el-button v-if="canWrite" link type="primary" :icon="Edit" @click="openAttrDialog(row)" />
                  <el-button v-if="canDelete" link type="danger" :icon="Delete" @click="deleteAttr(row)" />
                </template>
              </el-table-column>
            </el-table>

            <div class="flex justify-end border-t border-slate-100 px-4 py-4">
              <el-pagination
                v-model:current-page="attrPagination.page"
                v-model:page-size="attrPagination.size"
                :page-sizes="[10, 20, 50]"
                :total="attrPagination.total"
                layout="total, sizes, prev, pager, next"
                @change="loadAttributes"
              />
            </div>
          </div>
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <DimensionFormDialog
      v-model="dimensionDialogVisible"
      :data="currentDimension"
      @success="handleDimensionSaved"
    />
    <UnitFormDialog
      v-model="unitDialogVisible"
      :data="currentUnit"
      :selected-dimension="selectedDimension"
      :base-unit="baseUnit"
      :conversions="conversionList"
      @success="handleUnitSaved"
    />
    <AttrFormDialog
      v-model="attrDialogVisible"
      :data="currentAttr"
      @success="handleAttrSaved"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete, Edit, Plus, RefreshRight, Search } from '@element-plus/icons-vue'
import DimensionFormDialog from '@/components/master-data/DimensionFormDialog.vue'
import UnitFormDialog from '@/components/master-data/UnitFormDialog.vue'
import AttrFormDialog from '@/components/master-data/AttrFormDialog.vue'
import { useDictionaryStore } from '@/stores/dictionaries'
import {
  attrDefinitionApi,
  ResourceType,
  unitApi,
  unitConversionApi,
  unitDimensionApi,
} from '@/api/masterData'
import type { AttrDefinition, AttrDataType, ResourceType as ResourceTypeValue, Unit, UnitConversion, UnitDimension } from '@/api/masterData'

interface UnitQueryState {
  keyword: string
  unitType: 'ALL' | 'BASE' | 'CONVERTED'
}

interface AttrQueryState {
  keyword: string
  dataType: AttrDataType | undefined
  resourceType: ResourceType | undefined
}

interface PaginationState {
  page: number
  size: number
  total: number
}

const activeTab = ref<'units' | 'attributes'>('units')
const canWrite = computed(() => true)
const canDelete = computed(() => true)
const dictionaryStore = useDictionaryStore()
const summaryStats = reactive({
  dimensions: 0,
  units: 0,
  attributes: 0,
})

const dimensionKeyword = ref('')
const dimensionLoading = ref(false)
const dimensionList = ref<UnitDimension[]>([])
const selectedDimensionId = ref<number | null>(null)
const currentDimension = ref<UnitDimension | null>(null)
const dimensionDialogVisible = ref(false)

const unitLoading = ref(false)
const unitList = ref<Unit[]>([])
const allUnitsInDimension = ref<Unit[]>([])
const conversionList = ref<UnitConversion[]>([])
const currentUnit = ref<Unit | null>(null)
const unitDialogVisible = ref(false)
const unitPagination = reactive<PaginationState>({ page: 1, size: 10, total: 0 })
const unitQuery = reactive<UnitQueryState>({
  keyword: '',
  unitType: 'ALL',
})

const attrLoading = ref(false)
const attrList = ref<AttrDefinition[]>([])
const currentAttr = ref<AttrDefinition | null>(null)
const attrDialogVisible = ref(false)
const attrPagination = reactive<PaginationState>({ page: 1, size: 10, total: 0 })
const attrQuery = reactive<AttrQueryState>({
  keyword: '',
  dataType: undefined,
  resourceType: undefined,
})

const attrDataTypeOptions = computed<Array<{ label: string; value: AttrDataType }>>(() =>
  dictionaryStore.getOptions('ATTR_DATA_TYPE').map((item) => ({
    label: item.label,
    value: item.value as AttrDataType,
  })),
)

const resourceTypeOptions = computed<Array<{ label: string; value: ResourceTypeValue }>>(() =>
  dictionaryStore.getOptions('RESOURCE_TYPE').map((item) => ({
    label: item.label,
    value: item.value as ResourceTypeValue,
  })),
)

const unitKindOptions = computed<Array<{ label: string; value: 'BASE' | 'CONVERTED' }>>(() =>
  dictionaryStore.getOptions('UNIT_KIND').map((item) => ({
    label: item.label,
    value: item.value as 'BASE' | 'CONVERTED',
  })),
)

const selectedDimension = computed<UnitDimension | null>(() => {
  return dimensionList.value.find((item: UnitDimension) => item.id === selectedDimensionId.value) ?? null
})

const baseUnit = computed<Unit | null>(() => {
  return allUnitsInDimension.value.find((item: Unit) => item.is_base) ?? null
})

const conversionFactorMap = computed<Record<number, number>>(() => {
  const result: Record<number, number> = {}
  const currentBaseUnit = baseUnit.value
  if (!currentBaseUnit) {
    return result
  }

  for (const unit of allUnitsInDimension.value) {
    if (unit.is_base) {
      result[unit.id] = 1
      continue
    }

    const direct = conversionList.value.find(
      (item: UnitConversion) => item.from_unit.id === unit.id && item.to_unit.id === currentBaseUnit.id,
    )
    if (direct) {
      result[unit.id] = Number(direct.conversion_factor)
      continue
    }

    const reverse = conversionList.value.find(
      (item: UnitConversion) => item.from_unit.id === currentBaseUnit.id && item.to_unit.id === unit.id,
    )
    if (reverse) {
      const factor = Number(reverse.conversion_factor)
      if (factor > 0) {
        result[unit.id] = 1 / factor
      }
    }
  }

  return result
})

function formatDate(value: string): string {
  return new Date(value).toLocaleString('zh-CN', { hour12: false })
}

function formatFactor(value: number | undefined): string {
  if (value === undefined) {
    return '未配置'
  }
  return Number(value).toFixed(6).replace(/\.?0+$/, '')
}

function getAttrDataTypeLabel(value: AttrDataType): string {
  return dictionaryStore.getLabel('ATTR_DATA_TYPE', value)
}

function getResourceTypeLabel(value: ResourceTypeValue): string {
  return dictionaryStore.getLabel('RESOURCE_TYPE', value)
}

function isAttrApplicableToAll(values: ResourceTypeValue[]): boolean {
  const allTypes = resourceTypeOptions.value.map((item) => item.value)
  return allTypes.length > 0 && allTypes.every((item) => values.includes(item))
}

function getDisplayApplicableResourceTypes(values: ResourceTypeValue[]): ResourceTypeValue[] {
  return isAttrApplicableToAll(values) ? [] : values
}

function getAttrResourceTagType(value: ResourceTypeValue): 'primary' | 'success' | 'warning' | 'info' {
  if (value === ResourceType.MATERIAL) {
    return 'primary'
  }
  if (value === ResourceType.EQUIPMENT) {
    return 'success'
  }
  return 'info'
}

function getUnitKindLabel(value: 'BASE' | 'CONVERTED'): string {
  return dictionaryStore.getLabel('UNIT_KIND', value)
}

function formatUnitFormula(unit: Unit): string {
  const currentBaseUnit = baseUnit.value
  const factor = conversionFactorMap.value[unit.id]
  if (!currentBaseUnit || factor === undefined) {
    return '尚未配置相对基准单位的换算关系'
  }
  return `1 ${unit.symbol || unit.code} = ${formatFactor(factor)} ${currentBaseUnit.symbol || currentBaseUnit.code}`
}

function handleUnitFilter() {
  unitPagination.page = 1
  loadUnitsAndConversions()
}

function handleAttrFilter() {
  attrPagination.page = 1
  loadAttributes()
}

function selectDimension(dimensionId: number) {
  if (selectedDimensionId.value === dimensionId) {
    return
  }
  selectedDimensionId.value = dimensionId
  unitPagination.page = 1
  void loadUnitsAndConversions()
}

async function loadDimensions(preserveSelection = true) {
  dimensionLoading.value = true
  try {
    const response = await unitDimensionApi.list({
      keyword: dimensionKeyword.value || undefined,
      page: 1,
      size: 200,
    })
    dimensionList.value = response.data.items

    if (dimensionList.value.length === 0) {
      selectedDimensionId.value = null
      unitList.value = []
      allUnitsInDimension.value = []
      conversionList.value = []
      unitPagination.total = 0
      return
    }

    const stillExists = preserveSelection
      ? dimensionList.value.some((item: UnitDimension) => item.id === selectedDimensionId.value)
      : false
    selectedDimensionId.value = stillExists ? selectedDimensionId.value : dimensionList.value[0].id
    await loadUnitsAndConversions()
  } catch {
    ElMessage.error('加载量纲列表失败')
  } finally {
    dimensionLoading.value = false
  }
}

async function loadSummaryStats() {
  try {
    const [dimensionResponse, unitResponse, attrResponse] = await Promise.all([
      unitDimensionApi.list({ page: 1, size: 1 }),
      unitApi.list({ page: 1, size: 1 }),
      attrDefinitionApi.list({ page: 1, size: 1 }),
    ])

    summaryStats.dimensions = dimensionResponse.data.total
    summaryStats.units = unitResponse.data.total
    summaryStats.attributes = attrResponse.data.total
  } catch (error) {
    console.error('Failed to load dictionary summary stats:', error)
  }
}

async function loadUnitsAndConversions() {
  if (!selectedDimensionId.value) {
    unitList.value = []
    allUnitsInDimension.value = []
    conversionList.value = []
    unitPagination.total = 0
    return
  }

  unitLoading.value = true
  try {
    const isBase =
      unitQuery.unitType === 'ALL'
        ? undefined
        : unitQuery.unitType === 'BASE'
          ? true
          : false

    const [pageResponse, allResponse, conversionResponse] = await Promise.all([
      unitApi.list({
        keyword: unitQuery.keyword || undefined,
        dimension_id: selectedDimensionId.value,
        is_base: isBase,
        page: unitPagination.page,
        size: unitPagination.size,
      }),
      unitApi.list({
        dimension_id: selectedDimensionId.value,
        page: 1,
        size: 500,
      }),
      unitConversionApi.list({ page: 1, size: 500 }),
    ])

    unitList.value = pageResponse.data.items
    unitPagination.total = pageResponse.data.total
    allUnitsInDimension.value = allResponse.data.items

    const unitIds = new Set(allUnitsInDimension.value.map((item: Unit) => item.id))
    conversionList.value = conversionResponse.data.items.filter(
      (item: UnitConversion) => unitIds.has(item.from_unit.id) && unitIds.has(item.to_unit.id),
    )
  } catch {
    ElMessage.error('加载单位数据失败')
  } finally {
    unitLoading.value = false
  }
}

async function loadAttributes() {
  attrLoading.value = true
  try {
    const response = await attrDefinitionApi.list({
      keyword: attrQuery.keyword || undefined,
      data_type: attrQuery.dataType,
      resource_type: attrQuery.resourceType,
      page: attrPagination.page,
      size: attrPagination.size,
    })
    attrList.value = response.data.items
    attrPagination.total = response.data.total
  } catch {
    ElMessage.error('加载柔性属性失败')
  } finally {
    attrLoading.value = false
  }
}

function openDimensionDialog(item?: UnitDimension) {
  currentDimension.value = item ?? null
  dimensionDialogVisible.value = true
}

function openUnitDialog(item?: Unit) {
  currentUnit.value = item ?? null
  unitDialogVisible.value = true
}

function openAttrDialog(item?: AttrDefinition) {
  currentAttr.value = item ?? null
  attrDialogVisible.value = true
}

async function deleteDimension(item: UnitDimension) {
  try {
    await ElMessageBox.confirm(`确定删除量纲“${item.name}（${item.code}）”吗？`, '删除确认', {
      type: 'warning',
    })
    await unitDimensionApi.remove(item.id)
    ElMessage.success('量纲已删除')
    await Promise.all([loadDimensions(false), loadSummaryStats()])
  } catch (error: unknown) {
    if (error === 'cancel' || error === 'close') {
      return
    }
  }
}

async function deleteUnit(item: Unit) {
  try {
    await ElMessageBox.confirm(`确定删除单位“${item.name}（${item.code}）”吗？`, '删除确认', {
      type: 'warning',
    })

    const relatedConversions = conversionList.value.filter(
      (conversion: UnitConversion) =>
        conversion.from_unit.id === item.id || conversion.to_unit.id === item.id,
    )
    for (const conversion of relatedConversions) {
      await unitConversionApi.remove(conversion.id)
    }

    await unitApi.remove(item.id)
    ElMessage.success('单位已删除')
    await Promise.all([loadUnitsAndConversions(), loadSummaryStats()])
  } catch (error: unknown) {
    if (error === 'cancel' || error === 'close') {
      return
    }
  }
}

async function deleteAttr(item: AttrDefinition) {
  try {
    await ElMessageBox.confirm(`确定删除属性“${item.name}（${item.code}）”吗？`, '删除确认', {
      type: 'warning',
    })
    await attrDefinitionApi.remove(item.id)
    ElMessage.success('柔性属性已删除')
    await Promise.all([loadAttributes(), loadSummaryStats()])
  } catch (error: unknown) {
    if (error === 'cancel' || error === 'close') {
      return
    }
  }
}

async function handleDimensionSaved() {
  await Promise.all([loadDimensions(), loadSummaryStats()])
}

async function handleUnitSaved() {
  await Promise.all([loadUnitsAndConversions(), loadSummaryStats()])
}

async function handleAttrSaved() {
  await Promise.all([loadAttributes(), loadSummaryStats()])
}

onMounted(() => {
  void dictionaryStore.ensureLoaded()
  void loadDimensions(false)
  void loadAttributes()
  void loadSummaryStats()
})
</script>

<style scoped>
.dictionary-page {
  background:
    radial-gradient(circle at top right, rgba(14, 165, 233, 0.08), transparent 22%),
    linear-gradient(180deg, rgba(248, 250, 252, 0.9), rgba(241, 245, 249, 0.5));
}

.stat-label {
  font-size: 0.72rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: rgb(100 116 139);
}

.stat-value {
  margin-top: 0.1rem;
  font-size: 1.25rem;
  font-weight: 600;
  color: rgb(15 23 42);
}

.header-stats :deep(.el-divider--vertical) {
  height: 28px;
  margin: 0 0.15rem;
}

.header-stat-item {
  display: flex;
  min-width: 72px;
  flex-direction: column;
  gap: 0.1rem;
}

.dimension-create-button {
  border-style: dashed;
  border-color: rgb(148 163 184);
  color: rgb(15 23 42);
  background: rgba(255, 255, 255, 0.92);
}

.dimension-create-button:hover {
  border-color: var(--el-color-primary);
  color: var(--el-color-primary);
}

.dimension-menu {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  margin: 0;
  padding: 0;
  list-style: none;
}

.dimension-menu__item {
  position: relative;
  display: flex;
  width: 100%;
  align-items: center;
  gap: 0.75rem;
  border: 1px solid transparent;
  border-left: 3px solid transparent;
  border-radius: 0.9rem;
  background: transparent;
  padding: 0.8rem 0.85rem 0.8rem 0.7rem;
  transition: background-color 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
}

.dimension-menu__item:hover {
  background: rgba(248, 250, 252, 0.95);
  border-color: rgb(226 232 240);
}

.dimension-menu__item--active {
  border-color: rgba(59, 130, 246, 0.12);
  border-left-color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
  box-shadow: 0 10px 20px rgba(37, 99, 235, 0.08);
}

.dimension-menu__actions {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  opacity: 0;
  transform: translateX(4px);
  pointer-events: none;
  transition: opacity 0.18s ease, transform 0.18s ease;
}

.dimension-menu__item:hover .dimension-menu__actions {
  opacity: 1;
  transform: translateX(0);
  pointer-events: auto;
}

.dimension-menu__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 999px;
  background: transparent;
  color: rgb(100 116 139);
  transition: background-color 0.18s ease, color 0.18s ease;
}

.dimension-menu__icon:hover {
  background: rgba(226, 232, 240, 0.9);
}

.dimension-menu__icon--edit:hover {
  color: var(--el-color-primary);
}

.dimension-menu__icon--delete:hover {
  color: var(--el-color-danger);
}

.unit-formula-chip {
  display: inline-flex;
  max-width: 100%;
  align-items: center;
  border-radius: 0.65rem;
  background: rgb(241 245 249);
  padding: 0.4rem 0.65rem;
  font-family: ui-monospace, SFMono-Regular, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace;
  font-size: 0.78rem;
  color: rgb(30 41 59);
}

.page-header {
  backdrop-filter: blur(12px);
}
</style>

