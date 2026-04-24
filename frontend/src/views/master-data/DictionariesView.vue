<template>
  <div class="flex h-full min-h-0 flex-col gap-4 p-6 bg-[radial-gradient(circle_at_top_right,rgba(14,165,233,0.08),transparent_22%),linear-gradient(180deg,rgba(248,250,252,0.9),rgba(241,245,249,0.5))]">
    <PageHeader :stats="summaryStats" />

    <el-tabs v-model="activeTab" class="flex-1 min-h-0">
      <el-tab-pane label="计量单位管理" name="units" class="h-full">
        <div class="grid h-full min-h-0 gap-4 xl:grid-cols-[280px_minmax(0,1fr)]">
          <DimensionSidebar
            v-model:keyword="dimensionKeyword"
            :dimension-list="dimensionList"
            :selected-id="selectedDimensionId"
            :loading="dimensionLoading"
            :can-write="canWrite"
            :can-delete="canDelete"
            @select="selectDimension"
            @create="openDimensionDialog()"
            @edit="openDimensionDialog"
            @delete="deleteDimension"
            @refresh="loadDimensions(false)"
          />

          <UnitTablePanel
            v-model:query:keyword="unitQuery.keyword"
            v-model:query:unitType="unitQuery.unitType"
            v-model:pagination:page="unitPagination.page"
            v-model:pagination:size="unitPagination.size"
            :unit-list="unitList"
            :selected-dimension="selectedDimension"
            :base-unit="baseUnit"
            :query="unitQuery"
            :pagination="unitPagination"
            :loading="unitLoading"
            :can-write="canWrite"
            :can-delete="canDelete"
            :unit-kind-options="unitKindOptions"
            :conversion-factor-map="conversionFactorMap"
            @create="openUnitDialog()"
            @edit="openUnitDialog"
            @delete="deleteUnit"
            @filter="handleUnitFilter"
            @page-change="loadUnitsAndConversions"
          />
        </div>
      </el-tab-pane>

      <el-tab-pane label="柔性属性模板" name="attributes" class="h-full">
        <AttributeTablePanel
          v-model:query:keyword="attrQuery.keyword"
          v-model:query:dataType="attrQuery.dataType"
          v-model:query:resourceType="attrQuery.resourceType"
          v-model:pagination:page="attrPagination.page"
          v-model:pagination:size="attrPagination.size"
          :attr-list="attrList"
          :query="attrQuery"
          :pagination="attrPagination"
          :loading="attrLoading"
          :can-write="canWrite"
          :can-delete="canDelete"
          :data-type-options="attrDataTypeOptions"
          :resource-type-options="resourceTypeOptions"
          @create="openAttrDialog()"
          @edit="openAttrDialog"
          @delete="deleteAttr"
          @filter="handleAttrFilter"
          @page-change="loadAttributes"
        />
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
import PageHeader from '@/components/master-data/dictionaries/PageHeader.vue'
import DimensionSidebar from '@/components/master-data/dictionaries/DimensionSidebar.vue'
import UnitTablePanel from '@/components/master-data/dictionaries/UnitTablePanel.vue'
import AttributeTablePanel from '@/components/master-data/dictionaries/AttributeTablePanel.vue'
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
    await ElMessageBox.confirm(`确定删除量纲"${item.name}（${item.code}）"吗？`, '删除确认', {
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
    await ElMessageBox.confirm(`确定删除单位"${item.name}（${item.code}）"吗？`, '删除确认', {
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
    await ElMessageBox.confirm(`确定删除属性"${item.name}（${item.code}）"吗？`, '删除确认', {
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
