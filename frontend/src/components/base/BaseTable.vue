<template>
  <el-table
    ref="tableRef"
    :data="data"
    :loading="loading"
    :border="border"
    :stripe="stripe"
    :size="size"
    :height="height"
    :max-height="maxHeight"
    @selection-change="handleSelectionChange"
    @sort-change="handleSortChange"
  >
    <el-table-column v-if="showSelection" type="selection" width="55" fixed="left" />
    
    <el-table-column
      v-for="col in columns"
      :key="col.prop as string"
      :prop="col.prop"
      :label="col.label"
      :width="col.width"
      :min-width="col.minWidth"
      :fixed="col.fixed"
      :sortable="col.sortable"
      :align="col.align || 'left'"
    >
      <template v-if="col.slot" #default="scope">
        <slot :name="col.slot" :row="scope.row" :$index="scope.$index" />
      </template>
      <template v-else-if="col.formatter" #default="scope">
        {{ col.formatter(scope.row, col, scope.row[col.prop as keyof typeof scope.row], scope.$index) }}
      </template>
    </el-table-column>
    
    <el-table-column
      v-if="showActions"
      label="操作"
      :width="actionsWidth"
      :fixed="actionsFixed"
      align="center"
    >
      <template #default="scope">
        <slot name="actions" :row="scope.row" :$index="scope.$index" />
      </template>
    </el-table-column>
  </el-table>
  
  <div v-if="showPagination" class="pagination-wrapper">
    <el-pagination
      v-model:current-page="currentPage"
      v-model:page-size="currentPageSize"
      :total="total"
      :page-sizes="pageSizes"
      :layout="paginationLayout"
      @current-change="handlePageChange"
      @size-change="handleSizeChange"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import type { TableInstance } from 'element-plus'

export interface TableColumn {
  prop: string
  label: string
  width?: number | string
  minWidth?: number | string
  fixed?: 'left' | 'right' | boolean
  sortable?: boolean | 'custom'
  align?: 'left' | 'center' | 'right'
  slot?: string
  formatter?: (row: any, column: TableColumn, cellValue: any, index: number) => string
}

const props = withDefaults(defineProps<{
  data: any[]
  loading?: boolean
  columns: TableColumn[]
  border?: boolean
  stripe?: boolean
  size?: 'large' | 'default' | 'small'
  height?: string | number
  maxHeight?: string | number
  showSelection?: boolean
  showActions?: boolean
  actionsWidth?: number | string
  actionsFixed?: 'left' | 'right'
  showPagination?: boolean
  total?: number
  page?: number
  pageSize?: number
  pageSizes?: number[]
  paginationLayout?: string
}>(), {
  loading: false,
  border: true,
  stripe: true,
  size: 'default',
  showSelection: false,
  showActions: false,
  actionsWidth: 200,
  showPagination: true,
  total: 0,
  page: 1,
  pageSize: 20,
  pageSizes: () => [10, 20, 50, 100],
  paginationLayout: 'total, sizes, prev, pager, next, jumper',
})

const emit = defineEmits<{
  'selection-change': [selection: any[]]
  'sort-change': [sort: { prop: string; order: string }]
  'page-change': [page: number]
  'size-change': [size: number]
}>()

const tableRef = ref<TableInstance>()
const currentPage = ref(props.page)
const currentPageSize = ref(props.pageSize)

watch(() => props.page, (val) => { currentPage.value = val })
watch(() => props.pageSize, (val) => { currentPageSize.value = val })

function handleSelectionChange(selection: any[]) {
  emit('selection-change', selection)
}

function handleSortChange(sort: { prop: string; order: string }) {
  emit('sort-change', sort)
}

function handlePageChange(page: number) {
  emit('page-change', page)
}

function handleSizeChange(size: number) {
  emit('size-change', size)
}

defineExpose({
  tableRef,
})
</script>

<style scoped>
.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  padding: 16px 0;
}
</style>
