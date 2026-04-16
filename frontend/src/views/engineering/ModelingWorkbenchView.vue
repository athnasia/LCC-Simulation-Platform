<template>
  <div class="modeling-workbench">
    <!-- 顶部操作栏 -->
    <div class="workbench-header">
      <div class="header-left">
        <el-breadcrumb separator="/">
          <el-breadcrumb-item v-if="currentProject">
            {{ currentProject.name }}
          </el-breadcrumb-item>
          <el-breadcrumb-item v-if="currentProduct">
            {{ currentProduct.name }}
          </el-breadcrumb-item>
          <el-breadcrumb-item v-if="currentScheme">
            {{ currentScheme.name }}
          </el-breadcrumb-item>
          <el-breadcrumb-item v-if="currentSchemeVersion">
            版本 {{ currentSchemeVersion.version }}
          </el-breadcrumb-item>
        </el-breadcrumb>
        
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
import { computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useEngineeringStore } from '@/stores/engineering'
import BomTreePanel from '@/components/engineering/BomTreePanel.vue'
import ProcessRoutePanel from '@/components/engineering/ProcessRoutePanel.vue'
import RouteStepFormPanel from '@/components/engineering/RouteStepFormPanel.vue'

const router = useRouter()
const route = useRoute()
const store = useEngineeringStore()

// 从 Store 获取状态
const currentProject = computed(() => store.currentProject)
const currentProduct = computed(() => store.currentProduct)
const currentScheme = computed(() => store.currentScheme)
const currentSchemeVersion = computed(() => store.currentSchemeVersion)
const hasCurrentSchemeVersion = computed(() => store.hasCurrentSchemeVersion)
const isAllLeafNodesConfigured = computed(() => store.isAllLeafNodesConfigured)
const leafNodeStats = computed(() => store.leafNodeStats)
const canGenerateSnapshot = computed(() => store.canGenerateSnapshot)

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
      // 可以跳转到快照详情页或仿真配置页
      // router.push(`/engineering/snapshots/${result.snapshot_id}`)
    }
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') {
      console.error('Generate snapshot failed:', error)
    }
  }
}

// 初始化：从路由参数加载数据
onMounted(async () => {
  const { projectId, productId, schemeId, versionId } = route.query
  
  if (projectId) {
    await store.loadProject(Number(projectId))
  }
  
  if (productId) {
    await store.loadProduct(Number(productId))
  }
  
  if (schemeId) {
    await store.loadScheme(Number(schemeId))
    await store.loadSchemeVersions(Number(schemeId))
  }
  
  if (versionId) {
    await store.switchSchemeVersion(Number(versionId))
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
