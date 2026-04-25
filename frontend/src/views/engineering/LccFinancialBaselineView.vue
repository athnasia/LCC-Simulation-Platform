<template>
  <div class="flex flex-col h-full w-full min-h-0 p-6 gap-4">
    <el-card shadow="never" class="search-card">
      <el-form :model="queryState" inline class="search-form">
        <el-form-item label="规则名称">
          <el-input
            v-model="queryState.keyword"
            placeholder="搜索财务评估基准名称"
            clearable
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="风险拨备策略">
          <el-select
            v-model="queryState.risk_strategy"
            clearable
            placeholder="全部"
            class="w-40"
          >
            <el-option
              v-for="option in riskStrategyOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select
            v-model="queryState.is_active"
            clearable
            placeholder="全部"
            class="w-28"
          >
            <el-option label="启用" :value="true" />
            <el-option label="禁用" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form> </el-card
    ><el-card
      shadow="never"
      class="flex-1 flex flex-col min-h-0"
      :body-style="{
        padding: '0',
        display: 'flex',
        flexDirection: 'column',
        flex: 1,
        minHeight: 0,
      }"
    >
      <div
        class="p-4 border-b border-gray-100 flex justify-between items-center bg-white flex-shrink-0"
      >
        <div>
          <div class="text-base font-medium text-gray-800">LCC 财务评估基准列表</div>
          <div class="text-xs text-gray-400 mt-1">
            用于统一管理净现值测算所需的生命周期、折现、风险拨备与残值规则。
          </div>
        </div>
        <el-button v-if="canWrite" type="primary" :icon="Plus" @click="openCreateDialog"
          >新增基准</el-button
        >
      </div>
      <div class="flex-1 min-h-0 p-4">
        <el-table
          v-loading="loading"
          :data="baselineList"
          stripe
          height="100%"
          class="w-full"
        >
          <el-table-column prop="rule_name" label="规则名称" min-width="220" />
          <el-table-column label="生命周期" width="110" align="center">
            <template #default="{ row }">{{ row.lifecycle_years }} 年</template>
          </el-table-column>
          <el-table-column label="折现率" width="120" align="right">
            <template #default="{ row }">{{ formatPercent(row.discount_rate) }}</template>
          </el-table-column>
          <el-table-column label="维保递增率" width="140" align="right">
            <template #default="{ row }">{{
              formatPercent(row.corrosion_rate)
            }}</template>
          </el-table-column>
          <el-table-column label="风险拨备策略" width="140">
            <template #default="{ row }">
              <el-tag
                :type="row.risk_strategy === 'FIXED' ? 'success' : 'warning'"
                effect="plain"
              >
                {{ getRiskStrategyLabel(row.risk_strategy) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="拨备数值" width="140" align="right">
            <template #default="{ row }">{{ formatRiskValue(row) }}</template>
          </el-table-column>
          <el-table-column label="期末残值率" width="140" align="right">
            <template #default="{ row }">{{
              formatPercent(row.eol_salvage_rate)
            }}</template>
          </el-table-column>
          <el-table-column label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
                {{ row.is_active ? "启用" : "禁用" }}
              </el-tag>
            </template> </el-table-column
          ><el-table-column label="操作" width="160" fixed="right">
            <template #default="{ row }">
              <el-button v-if="canWrite" type="primary" link @click="openEditDialog(row)"
                >编辑</el-button
              >
              <el-button v-if="canDelete" type="danger" link @click="handleDelete(row)"
                >删除</el-button
              >
            </template>
          </el-table-column>
        </el-table>
      </div>

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
    <el-dialog
      v-model="dialogVisible"
      :title="dialogMode === 'create' ? '新增 LCC 财务评估基准' : '编辑 LCC 财务评估基准'"
      width="760px"
      destroy-on-close
    >
      <el-form
        ref="formRef"
        :model="formState"
        :rules="formRules"
        label-width="130px"
        class="baseline-form"
      >
        <el-row :gutter="20">
          <el-col :span="24">
            <el-form-item label="规则名称" prop="rule_name">
              <el-input
                v-model="formState.rule_name"
                placeholder="例如：涉氯化工高危基准"
                maxlength="100"
                show-word-limit
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="生命周期 (年)" prop="lifecycle_years">
              <div class="unit-input-row">
                <el-input-number
                  v-model="formState.lifecycle_years"
                  :min="1"
                  :step="1"
                  :precision="0"
                  controls-position="right"
                  class="unit-input-control"
                />
                <span class="unit-suffix">年</span>
              </div>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="折现率 (WACC)" prop="discount_rate">
              <div class="unit-input-row">
                <el-input-number
                  v-model="formState.discount_rate"
                  :min="0"
                  :step="0.1"
                  :precision="4"
                  controls-position="right"
                  class="unit-input-control"
                />
                <span class="unit-suffix">%</span>
              </div>
            </el-form-item>
          </el-col> </el-row
        ><el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="设备维保递增率" prop="corrosion_rate">
              <div class="unit-input-row">
                <el-input-number
                  v-model="formState.corrosion_rate"
                  :min="0"
                  :step="0.1"
                  :precision="4"
                  controls-position="right"
                  class="unit-input-control"
                />
                <span class="unit-suffix">%</span>
              </div>
              <div class="form-hint">用于设备老化导致的维保费逐年上升</div>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="风险拨备策略" prop="risk_strategy">
              <el-select v-model="formState.risk_strategy" class="w-full">
                <el-option
                  v-for="option in riskStrategyOptions"
                  :key="option.value"
                  :label="option.label"
                  :value="option.value"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="拨备数值" prop="risk_value">
              <div class="unit-input-row">
                <el-input-number
                  v-model="formState.risk_value"
                  :min="0"
                  :step="0.1"
                  :precision="4"
                  controls-position="right"
                  class="unit-input-control"
                />
                <span class="unit-suffix">{{ riskValueSuffix }}</span>
              </div>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="期末处置残值率" prop="eol_salvage_rate">
              <div class="unit-input-row">
                <el-input-number
                  v-model="formState.eol_salvage_rate"
                  :step="0.1"
                  :precision="4"
                  controls-position="right"
                  class="unit-input-control"
                />
                <span class="unit-suffix">%</span>
              </div>
              <div class="form-hint">可为负数，代表倒贴环保拆除费</div>
            </el-form-item>
          </el-col> </el-row
        ><el-form-item label="是否启用" prop="is_active">
          <el-switch
            v-model="formState.is_active"
            active-text="启用"
            inactive-text="禁用"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit"
          >保存</el-button
        >
      </template>
    </el-dialog>
  </div>
</template>
<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import {
  lccFinancialBaselineApi,
  type LccFinancialBaseline,
  type LccFinancialBaselineCreate,
  type LccFinancialBaselineQuery,
  type LccFinancialBaselineUpdate,
} from '@/api/costing'
import { useAuthStore } from '@/stores/auth'
const authStore = useAuthStore()
const canWrite = computed(() => authStore.hasPermissionScope('/costing/lcc-financial-baselines:write'))
const canDelete = computed(() => authStore.hasPermissionScope('/costing/lcc-financial-baselines:delete'))

const riskStrategyOptions = [
  { label: '固定金额', value: 'FIXED' },
  { label: 'OPEX百分比', value: 'PERCENTAGE' },
] as const

const loading = ref(false)
const submitting = ref(false)
const dialogVisible = ref(false)
const dialogMode = ref<'create' | 'edit'>('create')
const editingBaselineId = ref<number | null>(null)
const total = ref(0)
const baselineList = ref<LccFinancialBaseline[]>([])
const formRef = ref<FormInstance>()

const queryState = reactive<LccFinancialBaselineQuery>({
  keyword: '',
  risk_strategy: undefined,
  is_active: undefined,
  page: 1,
  size: 20,
})
const createDefaultFormState = (): LccFinancialBaselineCreate => ({
  rule_name: '',
  lifecycle_years: 15,
  discount_rate: 10,
  corrosion_rate: 4,
  risk_strategy: 'FIXED',
  risk_value: 0,
  eol_salvage_rate: 0,
  is_active: true,
})

const formState = reactive<LccFinancialBaselineCreate>(createDefaultFormState())

const formRules: FormRules<typeof formState> = {
  rule_name: [{ required: true, message: '请输入规则名称', trigger: 'blur' }],
  lifecycle_years: [{ required: true, message: '请输入生命周期年限', trigger: 'change' }],
  discount_rate: [{ required: true, message: '请输入折现率', trigger: 'change' }],
  corrosion_rate: [{ required: true, message: '请输入设备维保递增率', trigger: 'change' }],
  risk_strategy: [{ required: true, message: '请选择风险拨备策略', trigger: 'change' }],
  risk_value: [
    { required: true, message: '请输入拨备数值', trigger: 'change' },
    {
      validator: (_rule, value, callback) => {
        if (value === null || value === undefined || Number.isNaN(Number(value))) {
          callback(new Error('请输入有效的拨备数值'))
          return
        }
        if (Number(value) < 0) {
          callback(new Error('拨备数值不能为负数'))
          return
        }
        if (formState.risk_strategy === 'PERCENTAGE' && Number(value) > 100) {
          callback(new Error('按 OPEX 百分比计提时，拨备数值不能超过 100'))
          return
        }
        callback()
      },
      trigger: 'change',
    },
  ],
  eol_salvage_rate: [{ required: true, message: '请输入期末处置残值率', trigger: 'change' }],
}

const riskValueSuffix = computed(() => (formState.risk_strategy === 'FIXED' ? '元' : '%'))

function getRiskStrategyLabel(value: LccFinancialBaseline['risk_strategy']) {
  return riskStrategyOptions.find((item) => item.value === value)?.label ?? value
}

function formatPercent(value: number) {
  return `${Number(value).toFixed(2)}%`
}

function formatRiskValue(row: LccFinancialBaseline) {
  return `${Number(row.risk_value).toFixed(2)}${row.risk_strategy === 'FIXED' ? ' 元' : '%'}`
}

function resetFormState() {
  Object.assign(formState, createDefaultFormState())
  editingBaselineId.value = null
  formRef.value?.clearValidate()
}

async function fetchData() {
  loading.value = true
  try {
    const res = await lccFinancialBaselineApi.list(queryState)
    baselineList.value = res.data.items ?? []
    total.value = res.data.total ?? 0
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
  queryState.risk_strategy = undefined
  queryState.is_active = undefined
  handleSearch()
}

function openCreateDialog() {
  dialogMode.value = 'create'
  resetFormState()
  dialogVisible.value = true
}

function openEditDialog(baseline: LccFinancialBaseline) {
  dialogMode.value = 'edit'
  editingBaselineId.value = baseline.id
  Object.assign(formState, {
    rule_name: baseline.rule_name,
    lifecycle_years: baseline.lifecycle_years,
    discount_rate: Number(baseline.discount_rate),
    corrosion_rate: Number(baseline.corrosion_rate),
    risk_strategy: baseline.risk_strategy,
    risk_value: Number(baseline.risk_value),
    eol_salvage_rate: Number(baseline.eol_salvage_rate),
    is_active: baseline.is_active,
  })
  formRef.value?.clearValidate()
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!formRef.value) {
    return
  }
  await formRef.value.validate()
  submitting.value = true
  try {
    if (dialogMode.value === 'create') {
      await lccFinancialBaselineApi.create(formState)
      ElMessage.success('LCC 财务评估基准已创建')
    } else if (editingBaselineId.value !== null) {
      const payload: LccFinancialBaselineUpdate = {
        rule_name: formState.rule_name,
        lifecycle_years: formState.lifecycle_years,
        discount_rate: formState.discount_rate,
        corrosion_rate: formState.corrosion_rate,
        risk_strategy: formState.risk_strategy,
        risk_value: formState.risk_value,
        eol_salvage_rate: formState.eol_salvage_rate,
        is_active: formState.is_active,
      }
      await lccFinancialBaselineApi.update(editingBaselineId.value, payload)
      ElMessage.success('LCC 财务评估基准已更新')
    }
    dialogVisible.value = false
    handleSearch()
  } finally {
    submitting.value = false
  }
}
async function handleDelete(baseline: LccFinancialBaseline) {
  try {
    await ElMessageBox.confirm(
      `确定删除 LCC 财务评估基准【${baseline.rule_name}】吗？`,
      '删除确认',
      {
        type: 'warning',
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
      },
    )
    await lccFinancialBaselineApi.remove(baseline.id)
    ElMessage.success('LCC 财务评估基准已删除')
    fetchData()
  } catch (error) {
    if (error === 'cancel' || error === 'close') {
      return
    }
    throw error
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.search-form .el-form-item {
  margin-bottom: 0;
}

.baseline-form :deep(.el-form-item__content) {
  display: block;
}

.unit-input-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.unit-input-control {
  width: 100%;
}

.unit-suffix {
  min-width: 40px;
  color: #4b5563;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.04em;
}

.form-hint {
  margin-top: 6px;
  color: #6b7280;
  font-size: 12px;
  line-height: 1.6;
}
</style>
