<template>
  <div class="dictionary-page flex h-full min-h-0 flex-col gap-4 p-6">
    <div class="page-header flex flex-col gap-3 rounded-2xl border border-slate-200 bg-white/90 p-5 shadow-sm lg:flex-row lg:items-end lg:justify-between">
      <div>
        <p class="text-xs font-semibold uppercase tracking-[0.28em] text-sky-600">Module 02</p>
        <h2 class="mt-2 text-2xl font-semibold text-slate-900">基础字典与模板</h2>
        <p class="mt-2 max-w-3xl text-sm leading-6 text-slate-500">
          统一维护量纲、单位与柔性属性模板，确保材料台账、设备能力库与成本公式引擎使用同一套主数据底座。
        </p>
      </div>
      <div class="grid gap-3 rounded-2xl bg-slate-50 px-4 py-3 text-sm text-slate-600 sm:grid-cols-3 sm:gap-6">
        <div>
          <div class="stat-label">量纲</div>
          <div class="stat-value">{{ dimensionList.length }}</div>
        </div>
        <div>
          <div class="stat-label">当前量纲单位</div>
          <div class="stat-value">{{ allUnitsInDimension.length }}</div>
        </div>
        <div>
          <div class="stat-label">柔性属性</div>
          <div class="stat-value">{{ attrPagination.total }}</div>
        </div>
      </div>
    </div>

    <el-tabs v-model="activeTab" class="flex-1 min-h-0">
      <el-tab-pane label="计量单位管理" name="units" class="h-full">
        <div class="grid h-full min-h-0 gap-4 xl:grid-cols-[320px_minmax(0,1fr)]">
          <el-card shadow="never" class="min-h-0 border-slate-200" body-style="padding:16px; display:flex; flex-direction:column; min-height:0;">
            <template #header>
              <div class="flex items-center justify-between gap-3">
                <div>
                  <div class="text-base font-semibold text-slate-900">量纲选择</div>
                  <div class="mt-1 text-xs text-slate-500">先选量纲，再维护所属单位</div>
                </div>
                <el-button v-if="canWrite" type="primary" :icon="Plus" @click="openDimensionDialog()">
                  新建量纲
                </el-button>
              </div>
            </template>

            <div class="mb-4 flex items-center gap-2">
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
              <el-scrollbar max-height="calc(100vh - 340px)">
                <div v-if="dimensionList.length > 0" class="flex flex-col gap-3 pr-2">
                  <button
                    v-for="dimension in dimensionList"
                    :key="dimension.id"
                    type="button"
                    class="dimension-card text-left"
                    :class="{ 'dimension-card--active': selectedDimensionId === dimension.id }"
                    @click="selectDimension(dimension.id)"
                  >
                    <div class="flex items-start justify-between gap-3">
                      <div class="min-w-0">
                        <div class="truncate text-sm font-semibold text-slate-900">{{ dimension.name }}</div>
                        <div class="mt-1 text-xs uppercase tracking-[0.22em] text-slate-400">{{ dimension.code }}</div>
                      </div>
                      <div class="flex items-center gap-2">
                        <el-button
                          v-if="canWrite"
                          link
                          type="primary"
                          @click.stop="openDimensionDialog(dimension)"
                        >
                          编辑
                        </el-button>
                        <el-button
                          v-if="canDelete"
                          link
                          type="danger"
                          @click.stop="deleteDimension(dimension)"
                        >
                          删除
                        </el-button>
                      </div>
                    </div>
                    <div class="mt-3 flex items-center justify-between text-xs text-slate-500">
                      <span>排序 {{ dimension.sort_order }}</span>
                      <span>{{ formatDate(dimension.updated_at) }}</span>
                    </div>
                    <p class="mt-2 line-clamp-2 text-xs leading-5 text-slate-500">
                      {{ dimension.description || '暂无描述' }}
                    </p>
                  </button>
                </div>
                <el-empty v-else :image-size="56" description="暂无量纲数据" />
              </el-scrollbar>
            </div>
          </el-card>

          <el-card shadow="never" class="min-h-0 border-slate-200" body-style="padding:0; display:flex; flex-direction:column; min-height:0;">
            <template #header>
              <div class="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                <div>
                  <div class="text-base font-semibold text-slate-900">
                    {{ selectedDimension ? `${selectedDimension.name} 单位台账` : '单位台账' }}
                  </div>
                  <div class="mt-1 text-xs text-slate-500">
                    <template v-if="selectedDimension && baseUnit">
                      当前基准单位：{{ baseUnit.name }}（{{ baseUnit.symbol || baseUnit.code }}）
                    </template>
                    <template v-else-if="selectedDimension">
                      当前量纲尚未配置基准单位，请优先创建基准单位。
                    </template>
                    <template v-else>
                      请先在左侧选择量纲。
                    </template>
                  </div>
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
                      <div class="text-sm font-medium text-emerald-600">1（基准）</div>
                    </template>
                    <template v-else>
                      <div class="text-sm font-medium text-slate-800">
                        {{ formatFactor(conversionFactorMap[row.id]) }}
                      </div>
                      <div class="mt-1 text-xs text-slate-500">
                        {{ formatUnitFormula(row) }}
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
            <div class="flex flex-col gap-3 xl:flex-row xl:items-end xl:justify-between">
              <div>
                <div class="text-base font-semibold text-slate-900">柔性属性模板</div>
                <div class="mt-1 text-xs text-slate-500">
                  为材料、设备等资源定义可扩展属性，供主数据录入和公式解析引擎统一复用。
                </div>
              </div>
              <div class="flex flex-wrap items-center gap-2">
                <el-input
                  v-model="attrQuery.keyword"
                  class="w-64"
                  clearable
                  placeholder="搜索属性名称 / 编码"
                  :prefix-icon="Search"
                  @keyup.enter="handleAttrFilter"
                  @clear="handleAttrFilter"
                />
                <el-select v-model="attrQuery.dataType" clearable class="w-36" placeholder="数据类型" @change="handleAttrFilter">
                  <el-option
                    v-for="item in attrDataTypeOptions"
                    :key="item.value"
                    :label="item.label"
                    :value="item.value"
                  />
                </el-select>
                <el-select v-model="attrQuery.resourceType" clearable class="w-40" placeholder="资源类型" @change="handleAttrFilter">
                  <el-option
                    v-for="item in resourceTypeOptions"
                    :key="item.value"
                    :label="item.label"
                    :value="item.value"
                  />
                </el-select>
                <el-button v-if="canWrite" type="primary" :icon="Plus" @click="openAttrDialog()">
                  新建属性
                </el-button>
              </div>
            </div>
          </template>

          <div class="flex min-h-0 flex-1 flex-col">
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
                  <el-tag size="small" type="info">{{ getAttrDataTypeLabel(row.data_type) }}</el-tag>
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
                      v-for="type in row.applicable_resource_types"
                      :key="type"
                      size="small"
                      type="success"
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
                  <el-tag :type="row.is_required ? 'danger' : 'info'" size="small">
                    {{ row.is_required ? '是' : '否' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="updated_at" label="更新时间" width="168">
                <template #default="{ row }">
                  {{ formatDate(row.updated_at) }}
                </template>
              </el-table-column>
              <el-table-column label="操作" width="140" fixed="right">
                <template #default="{ row }">
                  <el-button v-if="canWrite" link type="primary" @click="openAttrDialog(row)">
                    编辑
                  </el-button>
                  <el-button v-if="canDelete" link type="danger" @click="deleteAttr(row)">
                    删除
                  </el-button>
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
import { Plus, RefreshRight, Search } from '@element-plus/icons-vue'
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
    await loadDimensions(false)
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
    await loadUnitsAndConversions()
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
    await loadAttributes()
  } catch (error: unknown) {
    if (error === 'cancel' || error === 'close') {
      return
    }
  }
}

async function handleDimensionSaved() {
  await loadDimensions()
}

async function handleUnitSaved() {
  await loadUnitsAndConversions()
}

async function handleAttrSaved() {
  await loadAttributes()
}

onMounted(() => {
  void dictionaryStore.ensureLoaded()
  void loadDimensions(false)
  void loadAttributes()
})
</script>

<style scoped>
.dictionary-page {
  background:
    radial-gradient(circle at top right, rgba(14, 165, 233, 0.08), transparent 22%),
    linear-gradient(180deg, rgba(248, 250, 252, 0.9), rgba(241, 245, 249, 0.5));
}

.stat-label {
  font-size: 0.75rem;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: rgb(100 116 139);
}

.stat-value {
  margin-top: 0.35rem;
  font-size: 1.5rem;
  font-weight: 600;
  color: rgb(15 23 42);
}

.dimension-card {
  border: 1px solid rgb(226 232 240);
  border-radius: 1rem;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(248, 250, 252, 0.96));
  padding: 1rem;
  transition: all 0.18s ease;
}

.dimension-card:hover {
  transform: translateY(-1px);
  border-color: rgb(125 211 252);
  box-shadow: 0 12px 24px rgba(15, 23, 42, 0.06);
}

.dimension-card--active {
  border-color: rgb(14 165 233);
  background: linear-gradient(180deg, rgba(240, 249, 255, 1), rgba(224, 242, 254, 0.78));
  box-shadow: 0 16px 30px rgba(14, 165, 233, 0.12);
}

.page-header {
  backdrop-filter: blur(12px);
}
</style>

