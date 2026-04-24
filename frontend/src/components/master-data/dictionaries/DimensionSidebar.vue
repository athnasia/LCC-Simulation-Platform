<template>
  <div class="flex min-h-0 flex-col rounded-2xl border border-slate-200/80 bg-white/80 p-3 shadow-sm">
    <el-button
      v-if="canWrite"
      plain
      :icon="Plus"
      class="mb-3 w-full !border-dashed !border-slate-400 !text-slate-900 !bg-white/92 hover:!border-primary hover:!text-primary"
      @click="$emit('create')"
    >
      新建量纲
    </el-button>

    <div class="mb-3 flex items-center gap-2">
      <el-input
        :model-value="keyword"
        clearable
        placeholder="搜索量纲名称 / 编码"
        :prefix-icon="Search"
        @update:model-value="$emit('update:keyword', $event)"
        @keyup.enter="$emit('refresh')"
        @clear="$emit('refresh')"
      />
      <el-button :icon="RefreshRight" @click="$emit('refresh')" />
    </div>

    <div v-loading="loading" class="min-h-0 flex-1 overflow-hidden">
      <el-scrollbar max-height="calc(100vh - 308px)">
        <ul v-if="dimensionList.length > 0" class="flex flex-col gap-[6px] m-0 p-0 list-none pr-1">
          <li v-for="dimension in dimensionList" :key="dimension.id">
            <button
              type="button"
              class="group relative flex w-full items-center gap-3 rounded-[0.9rem] border border-transparent border-l-[3px] bg-transparent px-[0.85rem] py-3 pl-[0.7rem] transition-all duration-200 hover:bg-slate-50/95 hover:border-slate-200"
              :class="{ '!border-blue-100/50 !border-l-primary !bg-primary-50/50 !shadow-lg !shadow-blue-500/10': selectedId === dimension.id }"
              @click="$emit('select', dimension.id)"
            >
              <div class="min-w-0 flex-1 text-left">
                <div class="truncate text-sm font-semibold text-slate-900">{{ dimension.name }}</div>
                <div class="mt-0.5 truncate text-[11px] uppercase tracking-[0.22em] text-slate-400">
                  {{ dimension.code }}
                </div>
              </div>
              <div class="flex items-center gap-1 opacity-0 translate-x-1 pointer-events-none transition-all duration-200 group-hover:opacity-100 group-hover:translate-x-0 group-hover:pointer-events-auto">
                <button
                  v-if="canWrite"
                  type="button"
                  class="inline-flex items-center justify-center w-7 h-7 border-none rounded-full bg-transparent text-slate-500 transition-all duration-200 hover:bg-slate-200/90 hover:text-primary"
                  @click.stop="$emit('edit', dimension)"
                >
                  <el-icon><Edit /></el-icon>
                </button>
                <button
                  v-if="canDelete"
                  type="button"
                  class="inline-flex items-center justify-center w-7 h-7 border-none rounded-full bg-transparent text-slate-500 transition-all duration-200 hover:bg-slate-200/90 hover:text-danger"
                  @click.stop="$emit('delete', dimension)"
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
</template>

<script setup lang="ts">
import { Delete, Edit, Plus, RefreshRight, Search } from '@element-plus/icons-vue'
import type { UnitDimension } from '@/api/masterData'

defineProps<{
  dimensionList: UnitDimension[]
  selectedId: number | null
  keyword: string
  loading: boolean
  canWrite: boolean
  canDelete: boolean
}>()

defineEmits<{
  (e: 'select', id: number): void
  (e: 'create'): void
  (e: 'edit', dimension: UnitDimension): void
  (e: 'delete', dimension: UnitDimension): void
  (e: 'refresh'): void
  (e: 'update:keyword', value: string): void
}>()
</script>
