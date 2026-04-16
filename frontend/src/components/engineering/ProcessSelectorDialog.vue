<template>
  <el-dialog
    v-model="visible"
    title="选择标准工序"
    width="800px"
    :close-on-click-modal="false"
  >
    <!-- 搜索栏 -->
    <div class="search-bar">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索工序名称或编码"
        clearable
        style="width: 300px"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
    </div>
    
    <!-- 工序列表 -->
    <el-table
      v-loading="loading"
      :data="filteredProcesses"
      highlight-current-row
      @current-change="handleCurrentChange"
      style="width: 100%; margin-top: 16px"
      max-height="400"
    >
      <el-table-column prop="name" label="工序名称" min-width="150" />
      
      <el-table-column prop="code" label="工序编码" width="120" />
      
      <el-table-column prop="setup_time" label="准备工时(h)" width="120" align="center">
        <template #default="{ row }">
          {{ row.setup_time || '-' }}
        </template>
      </el-table-column>
      
      <el-table-column prop="standard_time" label="运行工时(h)" width="120" align="center">
        <template #default="{ row }">
          {{ row.standard_time || '-' }}
        </template>
      </el-table-column>
      
      <el-table-column prop="description" label="描述" min-width="150">
        <template #default="{ row }">
          {{ row.description || '-' }}
        </template>
      </el-table-column>
    </el-table>
    
    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button 
        type="primary" 
        :disabled="!selectedProcess"
        @click="handleConfirm"
      >
        确定
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { processApi } from '@/api/masterData'
import type { Process } from '@/api/masterData'

interface Props {
  modelValue: boolean
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'select': [processId: number]
}>()

// 弹窗可见性
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})

// 搜索关键字
const searchKeyword = ref('')

// 加载状态
const loading = ref(false)

// 工序列表
const processes = ref<Process[]>([])

// 选中的工序
const selectedProcess = ref<Process | null>(null)

// 过滤后的工序列表
const filteredProcesses = computed(() => {
  if (!searchKeyword.value) {
    return processes.value
  }
  
  const keyword = searchKeyword.value.toLowerCase()
  return processes.value.filter(process => 
    process.name.toLowerCase().includes(keyword) ||
    process.code.toLowerCase().includes(keyword)
  )
})

// 当前行变化
function handleCurrentChange(currentRow: Process | null) {
  selectedProcess.value = currentRow
}

// 确认选择
function handleConfirm() {
  if (selectedProcess.value) {
    emit('select', selectedProcess.value.id)
    handleClose()
  }
}

// 关闭弹窗
function handleClose() {
  visible.value = false
  selectedProcess.value = null
  searchKeyword.value = ''
}

// 加载标准工艺列表
async function loadProcesses() {
  loading.value = true
  try {
    const res = await processApi.list({ size: 100 })
    processes.value = res.data.items || []
  } catch (error) {
    console.error('Failed to load processes:', error)
  } finally {
    loading.value = false
  }
}

// 监听弹窗打开
watch(visible, (newVal) => {
  if (newVal) {
    loadProcesses()
  }
})
</script>

<style scoped>
.search-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

:deep(.el-table__row) {
  cursor: pointer;
}
</style>
