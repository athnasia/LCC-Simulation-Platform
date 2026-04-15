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
        <el-form-item label="能源类型">
          <el-select v-model="queryState.energy_type" placeholder="请选择" clearable class="w-32">
            <el-option
              v-for="item in energyTypeOptions"
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
        <span class="text-base font-medium">能源日历列表</span>
        <el-button type="primary" :icon="Plus" @click="openCreateDialog">新增能源费率</el-button>
      </div>

      <!-- 表格 -->
      <div class="flex-1 min-h-0 relative p-4">
        <!-- 注意：后端为一(EnergyRate)对多(EnergyCalendar)，我们在这里展示 EnergyRate 表格，行展开展示时段明细 -->
        <el-table
          v-loading="loading"
          :data="energyList"
          stripe
          class="w-full flex-1"
          height="100%"
          row-key="id"
        >
          <el-table-column type="expand">
            <template #default="{ row }">
              <div class="p-4 bg-gray-50">
                <p class="mb-2 font-bold text-gray-600">日历时段配置：</p>
                <el-table :data="row.calendars" border size="small" class="w-full max-w-3xl">
                  <el-table-column prop="name" label="时段名称" width="120" />
                  <el-table-column label="生效时间" width="200">
                    <template #default="{ row: cal }">
                      {{ formatTime(cal.start_time) }} - {{ formatTime(cal.end_time) }}
                      <el-tag v-if="cal.start_time >= cal.end_time" type="warning" size="small" class="ml-1">跨天</el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column label="费率系数" width="100" align="right">
                    <template #default="{ row: cal }">x {{ Number(cal.multiplier).toFixed(2) }}</template>
                  </el-table-column>
                  <el-table-column label="实际执行单价" width="120" align="right">
                    <template #default="{ row: cal }">¥ {{ (Number(row.unit_price) * Number(cal.multiplier)).toFixed(4) }}</template>
                  </el-table-column>
                </el-table>
              </div>
            </template>
          </el-table-column>

          <el-table-column prop="code" label="能源编码" width="120" />
          <el-table-column prop="name" label="能源名称" min-width="150" />
          <el-table-column label="能源类型" width="120">
            <template #default="{ row }">
              <el-tag :type="getEnergyTypeTagType(row.energy_type)">
                {{ getEnergyTypeLabel(row.energy_type) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="基础单价" width="120" align="right">
            <template #default="{ row }">
               <span v-if="row.unit_price !== null">¥{{ Number(row.unit_price).toFixed(4) }}</span>
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

    <EnergyFormDialog
      v-model="dialogVisible"
      :data="currentEnergy"
      @success="handleSearch"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import { energyApi } from '@/api/masterData'
import type { EnergyRate, EnergyRateQuery } from '@/api/masterData'
import EnergyFormDialog from '@/components/master-data/EnergyFormDialog.vue'
import { useDictionaryStore } from '@/stores/dictionaries'
import { ENERGY_TYPE_OPTIONS } from '@/constants/systemDictionaries'

const dictionaryStore = useDictionaryStore()
const energyTypeOptions = computed(() => dictionaryStore.getOptions('ENERGY_TYPE', ENERGY_TYPE_OPTIONS))

const loading = ref(false)
const dialogVisible = ref(false)
const energyList = ref<EnergyRate[]>([])
const total = ref(0)
const currentEnergy = ref<EnergyRate | null>(null)

const queryState = reactive<EnergyRateQuery>({
  keyword: '',
  energy_type: undefined,
  is_active: undefined,
  page: 1,
  size: 20
})

function getEnergyTypeLabel(type: string) {
  return dictionaryStore.getLabel('ENERGY_TYPE', type, type, ENERGY_TYPE_OPTIONS)
}

function getEnergyTypeTagType(type: string) {
  return type === 'ELECTRICITY' ? 'primary' : type === 'WATER' ? 'success' : 'warning'
}

function formatTime(timeStr: string | null) {
  if (!timeStr) return '-'
  return timeStr.slice(0, 5) // "08:00:00" -> "08:00"
}

async function fetchData() {
  loading.value = true
  try {
    const res = await energyApi.listRates(queryState)
    energyList.value = res.data.items || []
    total.value = res.data.total || 0
  } catch (error) {
    console.error('Failed to fetch energy data:', error)
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
  queryState.energy_type = undefined
  queryState.is_active = undefined
  handleSearch()
}

function openCreateDialog() {
  currentEnergy.value = null
  dialogVisible.value = true
}

function openEditDialog(row: EnergyRate) {
  currentEnergy.value = { ...row }
  dialogVisible.value = true
}

async function handleDelete(row: EnergyRate) {
  try {
    await ElMessageBox.confirm(`确定要删除能源费率 [${row.name}] 吗？删除后相关的日历配置也将一并删除，且不可恢复。`, '危险操作', {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await energyApi.removeRate(row.id)
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
