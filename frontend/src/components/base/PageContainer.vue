<template>
  <div class="page-container">
    <div v-if="error" class="error-message">
      <el-alert :title="error" type="error" show-icon :closable="false" />
    </div>
    
    <div v-loading="loading" class="content-wrapper">
      <slot />
    </div>
    
    <div v-if="showEmpty && !loading && !error" class="empty-state">
      <el-empty :description="emptyText" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  loading?: boolean
  error?: string | null
  empty?: boolean
  emptyText?: string
}>(), {
  loading: false,
  error: null,
  empty: false,
  emptyText: '暂无数据',
})

const showEmpty = computed(() => props.empty)
</script>

<style scoped>
.page-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.error-message {
  margin-bottom: 16px;
}

.content-wrapper {
  flex: 1;
  overflow: auto;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 200px;
}
</style>
