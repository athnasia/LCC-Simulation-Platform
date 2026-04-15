<template>
  <div class="flex flex-col h-full w-full min-h-0 p-6 gap-4">
    <!-- 顶部搜索 -->
    <el-card shadow="never" class="search-card">
      <el-form :model="queryState" inline class="search-form">
        <el-form-item label="模糊搜索">
          <el-input
            v-model="queryState.keyword"
            placeholder="搜编码/名称"
            clearable
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="技能等级">
          <el-select v-model="queryState.skill_level" placeholder="请选择" clearable class="w-32">
            <el-option
              v-for="item in skillLevelOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="queryState.is_active" placeholder="全部" clearable class="w-24">
            <el-option label="启用" :value="true" />
            <el-option label="禁用" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 台账列表 -->
    <el-card shadow="never" class="flex-1 flex flex-col min-h-0" :body-style="{ padding: '0', display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0 }">
      <!-- 操作栏 -->
      <div class="p-4 border-b border-gray-100 flex justify-between items-center bg-white flex-shrink-0">
        <span class="text-base font-medium">人员工时列表</span>
        <el-button type="primary" :icon="Plus" @click="openCreateDialog">新增人员</el-button>
      </div>

      <!-- 表格 -->
      <div class="flex-1 min-h-0 relative p-4">
        <el-table
          v-loading="loading"
          :data="laborList"
          stripe
          class="w-full flex-1"
          height="100%"
        >
          <el-table-column prop="code" label="人员编码" width="120" />
          <el-table-column prop="name" label="人员名称" min-width="150" show-overflow-tooltip />
          <el-table-column label="工种" width="120">
            <template #default="{ row }">
              <span>{{ row.labor_type || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="技能等级" width="120">
            <template #default="{ row }">
              <el-tag :type="getSkillLevelTagType(row.skill_level)">
                {{ getSkillLevelLabel(row.skill_level) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="标准时薪" width="120" align="right">
            <template #default="{ row }">
              <span v-if="row.hourly_rate !== null">¥{{ Number(row.hourly_rate).toFixed(2) }}</span>
              <span v-else class="text-gray-400">-</span>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
                {{ row.is_active ? '启用' : '禁用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="140" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" link @click="openEditDialog(row)">编辑</el-button>
              <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 分页 -->
      <div class="p-3 border-t border-gray-100 bg-white flex justify-end flex-shrink-0">
        <el-pagination
          v-model:current-page="queryState.page"
          v-model:page-size="queryState.size"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          @size-change="handleSearch"
          @current-change="fetchData"
        />
      </div>
    </el-card>

    <LaborFormDialog
      v-model="dialogVisible"
      :data="currentLabor"
      @success="handleSearch"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import { laborApi } from '@/api/masterData'
import type { Labor, LaborQuery } from '@/api/masterData'
import LaborFormDialog from '@/components/master-data/LaborFormDialog.vue'
import { useDictionaryStore } from '@/stores/dictionaries'
import { LABOR_SKILL_OPTIONS } from '@/constants/systemDictionaries'

const dictionaryStore = useDictionaryStore()
const skillLevelOptions = computed(() => dictionaryStore.getOptions('LABOR_SKILL', LABOR_SKILL_OPTIONS))

const loading = ref(false)
const dialogVisible = ref(false)
const laborList = ref<Labor[]>([])
const total = ref(0)
const currentLabor = ref<Labor | null>(null)

const queryState = reactive<LaborQuery>({
  keyword: '',
  skill_level: undefined,
  is_active: undefined,
  page: 1,
  size: 20
})

function getSkillLevelLabel(level: string) {
  return dictionaryStore.getLabel('LABOR_SKILL', level, level, LABOR_SKILL_OPTIONS)
}

function getSkillLevelTagType(level: string) {
  switch (level) {
    case 'MASTER':
      return 'danger'
    case 'SENIOR':
      return 'warning'
    case 'INTERMEDIATE':
      return 'primary'
    case 'JUNIOR':
    default:
      return 'info'
  }
}

async function fetchData() {
  loading.value = true
  try {
    const res = await laborApi.list(queryState)
    laborList.value = res.data.items || []
    total.value = res.data.total || 0
  } catch (error) {
    console.error('Failed to fetch labor data:', error)
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  queryState.page = 1
  fetchData()
}

function handleReset() {
  queryState.keyword = ''
  queryState.skill_level = undefined
  queryState.is_active = undefined
  handleSearch()
}

function openCreateDialog() {
  currentLabor.value = null
  dialogVisible.value = true
}

function openEditDialog(row: Labor) {
  currentLabor.value = { ...row }
  dialogVisible.value = true
}

async function handleDelete(row: Labor) {
  try {
    await ElMessageBox.confirm(`确定要删除人员 [${row.name}] 吗？删除后不可恢复。`, '危险操作', {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await laborApi.remove(row.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch (error) {
    if (error === 'cancel' || error === 'close') {
      return
    }
    console.error('Delete failed:', error)
  }
}

onMounted(async () => {
  await dictionaryStore.ensureLoaded()
  fetchData()
})
</script>

<style scoped>
.search-form .el-form-item {
  margin-bottom: 0;
}
</style>
