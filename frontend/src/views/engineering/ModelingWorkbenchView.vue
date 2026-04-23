<template>
  <div class="modeling-workbench">
    <!-- 顶部操作栏 -->
    <div class="workbench-header">
      <div class="header-left">
        <!-- 级联选择器 -->
        <div class="cascade-selectors">
          <el-select
            v-model="selectedProjectId"
            placeholder="选择项目"
            clearable
            style="width: 180px"
            @change="handleProjectChange"
          >
            <el-option
              v-for="project in projects"
              :key="project.id"
              :label="project.name"
              :value="project.id"
            />
          </el-select>

          <el-select
            v-model="selectedProductId"
            placeholder="选择产品"
            clearable
            :disabled="!selectedProjectId"
            style="width: 180px"
            @change="handleProductChange"
          >
            <el-option
              v-for="product in products"
              :key="product.id"
              :label="product.name"
              :value="product.id"
            />
          </el-select>

          <el-select
            v-model="selectedSchemeId"
            placeholder="选择方案"
            clearable
            :disabled="!selectedProductId"
            style="width: 180px"
            @change="handleSchemeChange"
          >
            <el-option
              v-for="scheme in schemes"
              :key="scheme.id"
              :label="scheme.name"
              :value="scheme.id"
            />
          </el-select>

          <el-select
            v-model="selectedVersionId"
            placeholder="选择版本"
            clearable
            :disabled="!selectedSchemeId"
            style="width: 150px"
            @change="handleVersionChange"
          >
            <el-option
              v-for="version in schemeVersions"
              :key="version.id"
              :label="`版本 ${version.version}`"
              :value="version.id"
            />
          </el-select>
        </div>
        
        <div v-if="!hasCurrentSchemeVersion" class="no-version-hint">
          <el-text type="info">请先选择项目、产品和方案版本</el-text>
        </div>
      </div>
      
      <div class="header-right">
        <!-- 配置进度提示 -->
        <div v-if="hasCurrentSchemeVersion && leafNodeStats.total > 0" class="config-progress">
          <el-text :type="isAllLeafNodesConfigured ? 'success' : 'warning'">
            配置进度: {{ leafNodeStats.configured }}/{{ leafNodeStats.total }} 
            ({{ leafNodeStats.percentage }}%)
          </el-text>
          <el-progress 
            :percentage="leafNodeStats.percentage" 
            :status="isAllLeafNodesConfigured ? 'success' : 'warning'"
            :stroke-width="6"
            style="width: 120px; margin-left: 8px;"
          />
        </div>
        
        <el-button 
          type="primary" 
          :disabled="!canGenerateSnapshot"
          @click="handleGenerateSnapshot"
        >
          生成可计算快照
        </el-button>
      </div>
    </div>
    
    <!-- 三栏布局 -->
    <div class="workbench-body">
      <!-- 左栏：BOM 结构树 -->
      <div class="panel panel-left">
        <BomTreePanel />
      </div>
      
      <!-- 中栏：工艺路线编排 -->
      <div class="panel panel-center">
        <ProcessRoutePanel />
      </div>
      
      <!-- 右栏：资源参数表单 -->
      <div class="panel panel-right">
        <RouteStepFormPanel />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useEngineeringStore } from '@/stores/engineering'
import BomTreePanel from '@/components/engineering/BomTreePanel.vue'
import ProcessRoutePanel from '@/components/engineering/ProcessRoutePanel.vue'
import RouteStepFormPanel from '@/components/engineering/RouteStepFormPanel.vue'

const router = useRouter()
const route = useRoute()
const store = useEngineeringStore()

// 选择器状态
const selectedProjectId = ref<number | null>(null)
const selectedProductId = ref<number | null>(null)
const selectedSchemeId = ref<number | null>(null)
const selectedVersionId = ref<number | null>(null)

// 从 Store 获取状态
const projects = computed(() => store.projects)
const products = computed(() => store.products)
const schemes = computed(() => store.schemes)
const schemeVersions = computed(() => store.schemeVersions)
const currentSchemeVersion = computed(() => store.currentSchemeVersion)
const hasCurrentSchemeVersion = computed(() => store.hasCurrentSchemeVersion)
const isAllLeafNodesConfigured = computed(() => store.isAllLeafNodesConfigured)
const leafNodeStats = computed(() => store.leafNodeStats)
const canGenerateSnapshot = computed(() => store.canGenerateSnapshot)

// 项目选择变化
async function handleProjectChange(projectId: number | null) {
  selectedProductId.value = null
  selectedSchemeId.value = null
  selectedVersionId.value = null
  store.currentProduct = null
  store.currentScheme = null
  store.currentSchemeVersion = null
  store.products = []
  store.schemes = []
  store.schemeVersions = []
  store.bomTree = []
  
  if (projectId) {
    await store.loadProducts(projectId)
  }
}

// 产品选择变化
async function handleProductChange(productId: number | null) {
  selectedSchemeId.value = null
  selectedVersionId.value = null
  store.currentScheme = null
  store.currentSchemeVersion = null
  store.schemes = []
  store.schemeVersions = []
  store.bomTree = []
  
  if (productId) {
    await store.loadSchemes(productId)
  }
}

// 方案选择变化
async function handleSchemeChange(schemeId: number | null) {
  selectedVersionId.value = null
  store.currentSchemeVersion = null
  store.schemeVersions = []
  store.bomTree = []
  
  if (schemeId) {
    await store.loadSchemeVersions(schemeId)
  }
}

// 版本选择变化
async function handleVersionChange(versionId: number | null) {
  if (versionId) {
    await store.switchSchemeVersion(versionId)
  } else {
    store.currentSchemeVersion = null
    store.bomTree = []
  }
}

// 生成快照
async function handleGenerateSnapshot() {
  if (!currentSchemeVersion.value) {
    ElMessage.warning('请先选择方案版本')
    return
  }
  
  // 前置校验：检查是否所有叶子节点都已配置
  if (!isAllLeafNodesConfigured.value) {
    const stats = leafNodeStats.value
    ElMessage.error(
      `还有 ${stats.unconfigured} 个零件未配置工艺路线，无法生成快照。当前进度：${stats.configured}/${stats.total}`
    )
    return
  }
  
  try {
    const { value: snapshotName } = await ElMessageBox.prompt(
      '请输入快照名称',
      '生成可计算快照',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputPattern: /\S+/,
        inputErrorMessage: '快照名称不能为空',
      }
    )
    
    const result = await store.generateSnapshot({
      scheme_version_id: currentSchemeVersion.value.id,
      snapshot_name: snapshotName,
    })
    
    if (result) {
      ElMessage.success('快照生成成功')
    }
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') {
      console.error('Generate snapshot failed:', error)
    }
  }
}

// 初始化
onMounted(async () => {
  await store.loadProjects()
  
  const { projectId, productId, schemeId, versionId } = route.query
  
  if (schemeId && versionId) {
    const scheme = await store.loadScheme(Number(schemeId))
    if (scheme && scheme.product_id) {
      selectedSchemeId.value = Number(schemeId)
      
      const product = await store.loadProduct(scheme.product_id)
      if (product && product.project_id) {
        selectedProductId.value = scheme.product_id
        selectedProjectId.value = product.project_id
        
        await store.loadProducts(product.project_id)
        await store.loadSchemes(scheme.product_id)
      }
      
      await store.loadSchemeVersions(Number(schemeId))
      selectedVersionId.value = Number(versionId)
      await store.switchSchemeVersion(Number(versionId))
    }
  } else if (projectId) {
    selectedProjectId.value = Number(projectId)
    await store.loadProducts(Number(projectId))
    
    if (productId) {
      selectedProductId.value = Number(productId)
      await store.loadSchemes(Number(productId))
      
      if (schemeId) {
        selectedSchemeId.value = Number(schemeId)
        await store.loadSchemeVersions(Number(schemeId))
        
        if (versionId) {
          selectedVersionId.value = Number(versionId)
          await store.switchSchemeVersion(Number(versionId))
        }
      }
    }
  }
})
</script>

<style scoped>
.modeling-workbench {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 60px);
  background-color: #f5f7fa;
}

.workbench-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background-color: #fff;
  border-bottom: 1px solid #e4e7ed;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.cascade-selectors {
  display: flex;
  align-items: center;
  gap: 12px;
}

.no-version-hint {
  margin-left: 16px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.config-progress {
  display: flex;
  align-items: center;
}

.workbench-body {
  display: flex;
  flex: 1;
  overflow: hidden;
  padding: 16px;
  gap: 16px;
}

.panel {
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.panel-left {
  width: 25%;
  min-width: 280px;
}

.panel-center {
  width: 40%;
  min-width: 400px;
}

.panel-right {
  width: 35%;
  min-width: 320px;
}
</style>
