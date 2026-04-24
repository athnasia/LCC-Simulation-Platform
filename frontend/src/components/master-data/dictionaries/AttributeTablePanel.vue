<template>
  <el-card shadow="never" class="h-full flex flex-col min-h-0 flex-1 border-slate-200"
    body-style="padding:0; display:flex; flex-direction:column; flex:1; min-height:0;">
    <template #header>
      <div>
        <div class="text-base font-semibold text-slate-900">柔性属性模板</div>
        <div class="mt-1 text-xs text-slate-500">
          为材料、设备等资源定义可扩展属性，供主数据录入和公式解析引擎统一复用。
        </div>
      </div>
    </template>

    <div class="flex flex-wrap items-center justify-between gap-4 border-b border-slate-100 px-4 py-4">
      <div class="flex flex-wrap items-center gap-3">
        <el-input :model-value="query.keyword" class="w-[240px]" clearable placeholder="搜索属性名称 / 编码"
          :prefix-icon="Search" @update:model-value="$emit('update:query:keyword', $event)"
          @keyup.enter="$emit('filter')" @clear="$emit('filter')" />
        <el-select :model-value="query.dataType" clearable class="w-[160px]" placeholder="数据类型"
          @update:model-value="$emit('update:query:dataType', $event)" @change="$emit('filter')">
          <el-option v-for="item in dataTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
        <el-select :model-value="query.resourceType" clearable class="w-[160px]" placeholder="资源类型"
          @update:model-value="$emit('update:query:resourceType', $event)" @change="$emit('filter')">
          <el-option v-for="item in resourceTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
      </div>
      <div class="flex-shrink-0">
        <el-button v-if="canWrite" type="primary" :icon="Plus" @click="$emit('create')">
          新建属性
        </el-button>
      </div>
    </div>

    <div class="flex-1 min-h-0 overflow-hidden relative">
      <el-table v-loading="loading" :data="attrList" stripe height="100%">
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
              <el-tag v-if="isAttrApplicableToAll(row.applicable_resource_types)" size="small" type="warning"
                effect="light">
                适用全部
              </el-tag>
              <el-tag v-for="type in getDisplayApplicableResourceTypes(row.applicable_resource_types)" :key="type"
                size="small" :type="getAttrResourceTagType(type)" effect="light">
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
            <el-button v-if="canWrite" link type="primary" :icon="Edit" @click="$emit('edit', row)" />
            <el-button v-if="canDelete" link type="danger" :icon="Delete" @click="$emit('delete', row)" />
          </template>
        </el-table-column>
      </el-table>
    </div>

    <div class="flex justify-end border-t border-slate-100 px-4 py-4">
      <el-pagination :current-page="pagination.page" :page-size="pagination.size" :page-sizes="[10, 20, 50]"
        :total="pagination.total" layout="total, sizes, prev, pager, next"
        @update:current-page="$emit('update:pagination:page', $event)"
        @update:page-size="$emit('update:pagination:size', $event)" @change="$emit('page-change')" />
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { Delete, Edit, Plus, Search } from '@element-plus/icons-vue'
import { ResourceType } from '@/api/masterData'
import type { AttrDefinition, AttrDataType, ResourceType as ResourceTypeValue } from '@/api/masterData'
import { formatDate } from '@/utils/format'

interface AttrQuery {
  keyword: string
  dataType: AttrDataType | undefined
  resourceType: ResourceType | undefined
}

interface Pagination {
  page: number
  size: number
  total: number
}

interface DataTypeOption {
  label: string
  value: AttrDataType
}

interface ResourceTypeOption {
  label: string
  value: ResourceTypeValue
}

const props = defineProps<{
  attrList: AttrDefinition[]
  query: AttrQuery
  pagination: Pagination
  loading: boolean
  canWrite: boolean
  canDelete: boolean
  dataTypeOptions: DataTypeOption[]
  resourceTypeOptions: ResourceTypeOption[]
}>()

const emit = defineEmits<{
  (e: 'create'): void
  (e: 'edit', attr: AttrDefinition): void
  (e: 'delete', attr: AttrDefinition): void
  (e: 'filter'): void
  (e: 'page-change'): void
  (e: 'update:query:keyword', value: string): void
  (e: 'update:query:dataType', value: AttrDataType | undefined): void
  (e: 'update:query:resourceType', value: ResourceType | undefined): void
  (e: 'update:pagination:page', value: number): void
  (e: 'update:pagination:size', value: number): void
}>()

function getAttrDataTypeLabel(value: AttrDataType): string {
  const option = props.dataTypeOptions.find((item) => item.value === value)
  return option?.label ?? value
}

function getResourceTypeLabel(value: ResourceTypeValue): string {
  const option = props.resourceTypeOptions.find((item) => item.value === value)
  return option?.label ?? value
}

function isAttrApplicableToAll(values: ResourceTypeValue[]): boolean {
  const allTypes = props.resourceTypeOptions.map((item) => item.value)
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
</script>
