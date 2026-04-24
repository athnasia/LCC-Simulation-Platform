<template>
  <div class="flex flex-col gap-3 rounded-2xl border border-slate-200 bg-white/90 px-4 py-3 shadow-sm backdrop-blur-xl lg:flex-row lg:items-center lg:justify-between">
    <div class="min-w-0">
      <p class="text-[11px] font-semibold uppercase tracking-[0.28em] text-sky-600">Module 02</p>
      <h2 class="mt-1 text-2xl font-semibold text-slate-900">基础字典与模板</h2>
      <p class="mt-1 max-w-3xl text-sm leading-6 text-slate-500">
        统一维护量纲、单位与柔性属性模板，确保材料台账、设备能力库与成本公式引擎使用同一套主数据底座。
      </p>
    </div>
    <div class="flex items-center gap-2 rounded-xl border border-slate-200/80 bg-slate-50/90 px-3 py-2 text-sm text-slate-600 lg:flex-nowrap">
      <div class="flex min-w-[72px] flex-col gap-[2px]">
        <span class="text-[0.72rem] tracking-[0.12em] uppercase text-slate-500">量纲数</span>
        <span class="text-xl font-semibold text-slate-900">{{ stats.dimensions }}</span>
      </div>
      <el-divider direction="vertical" class="!h-7 !mx-1" />
      <div class="flex min-w-[72px] flex-col gap-[2px]">
        <span class="text-[0.72rem] tracking-[0.12em] uppercase text-slate-500">单位数</span>
        <span class="text-xl font-semibold text-slate-900">{{ stats.units }}</span>
      </div>
      <el-divider direction="vertical" class="!h-7 !mx-1" />
      <div class="flex min-w-[72px] flex-col gap-[2px]">
        <span class="text-[0.72rem] tracking-[0.12em] uppercase text-slate-500">属性数</span>
        <span class="text-xl font-semibold text-slate-900">{{ stats.attributes }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface SummaryStats {
  dimensions: number
  units: number
  attributes: number
}

defineProps<{
  stats: SummaryStats
}>()
</script>
