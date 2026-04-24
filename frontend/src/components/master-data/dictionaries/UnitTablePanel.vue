<template>
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
            :model-value="query.keyword"
            class="w-64"
            clearable
            placeholder="搜索单位名称 / 编码"
            :prefix-icon="Search"
            @update:model-value="$emit('update:query:keyword', $event)"
            @keyup.enter="$emit('filter')"
            @clear="$emit('filter')"
          />
          <el-select
            :model-value="query.unitType"
            class="w-36"
            @update:model-value="$emit('update:query:unitType', $event)"
            @change="$emit('filter')"
          >
            <el-option label="全部类型" value="ALL" />
            <el-option
              v-for="item in unitKindOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
          <el-button
            v-if="canWrite"
            type="primary"
            :icon="Plus"
            :disabled="!selectedDimension"
            @click="$emit('create')"
          >
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
        v-loading="loading"
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
              <div class="inline-flex max-w-full items-center rounded-[0.65rem] bg-slate-100 px-[0.65rem] py-2 font-mono text-[0.78rem] text-slate-700">
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
            <el-button v-if="canWrite" link type="primary" @click="$emit('edit', row)">
              编辑
            </el-button>
            <el-button v-if="canDelete" link type="danger" @click="$emit('delete', row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="flex justify-end border-t border-slate-100 px-4 py-4">
        <el-pagination
          :current-page="pagination.page"
          :page-size="pagination.size"
          :page-sizes="[10, 20, 50]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next"
          @update:current-page="$emit('update:pagination:page', $event)"
          @update:page-size="$emit('update:pagination:size', $event)"
          @change="$emit('page-change')"
        />
      </div>
    </div>
    <div v-else class="flex flex-1 items-center justify-center py-12">
      <el-empty description="请选择左侧量纲后开始维护单位" />
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { Plus, Search } from '@element-plus/icons-vue'
import type { Unit, UnitDimension } from '@/api/masterData'
import { formatDate, formatFactor } from '@/utils/format'

interface UnitQuery {
  keyword: string
  unitType: 'ALL' | 'BASE' | 'CONVERTED'
}

interface Pagination {
  page: number
  size: number
  total: number
}

interface UnitKindOption {
  label: string
  value: 'BASE' | 'CONVERTED'
}

const props = defineProps<{
  unitList: Unit[]
  selectedDimension: UnitDimension | null
  baseUnit: Unit | null
  query: UnitQuery
  pagination: Pagination
  loading: boolean
  canWrite: boolean
  canDelete: boolean
  unitKindOptions: UnitKindOption[]
  conversionFactorMap: Record<number, number>
}>()

const emit = defineEmits<{
  (e: 'create'): void
  (e: 'edit', unit: Unit): void
  (e: 'delete', unit: Unit): void
  (e: 'filter'): void
  (e: 'page-change'): void
  (e: 'update:query:keyword', value: string): void
  (e: 'update:query:unitType', value: 'ALL' | 'BASE' | 'CONVERTED'): void
  (e: 'update:pagination:page', value: number): void
  (e: 'update:pagination:size', value: number): void
}>()

function getUnitKindLabel(value: 'BASE' | 'CONVERTED'): string {
  const option = props.unitKindOptions.find((item) => item.value === value)
  return option?.label ?? value
}

function formatUnitFormula(unit: Unit): string {
  const currentBaseUnit = props.baseUnit
  const factor = props.conversionFactorMap[unit.id]
  if (!currentBaseUnit || factor === undefined) {
    return '尚未配置相对基准单位的换算关系'
  }
  return `1 ${unit.symbol || unit.code} = ${formatFactor(factor)} ${currentBaseUnit.symbol || currentBaseUnit.code}`
}
</script>
