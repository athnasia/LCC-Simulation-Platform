<template>
  <el-container class="app-layout h-screen overflow-hidden">
    <!-- ══════════════ 侧边栏 ══════════════ -->
    <el-aside
      :width="isCollapsed ? '64px' : '220px'"
      class="aside-wrapper transition-all duration-300 flex flex-col h-full overflow-hidden"
    >
      <!-- Logo 区 -->
      <div
        class="logo-area flex items-center h-16 px-4 flex-shrink-0 border-b border-gray-700 overflow-hidden"
      >
        <div class="logo-icon flex-shrink-0 w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center">
          <el-icon :size="18" color="#fff"><DataAnalysis /></el-icon>
        </div>
        <transition name="fade">
          <span
            v-if="!isCollapsed"
            class="ml-3 text-sm font-bold text-white whitespace-nowrap leading-tight"
          >
            工业互联网<br>
            <span class="text-xs font-normal text-indigo-400">LCC 仿真平台</span>
          </span>
        </transition>
      </div>

      <!-- 菜单 -->
      <el-scrollbar class="flex-1">
        <el-menu
          :default-active="currentPath"
          :collapse="isCollapsed"
          :collapse-transition="false"
          router
          background-color="#111827"
          text-color="#9ca3af"
          active-text-color="#818cf8"
          class="border-none menu-custom"
        >
          <!-- 1. 全景视界 -->
          <el-menu-item index="/dashboard">
            <el-icon><Monitor /></el-icon>
            <template #title>首页</template>
          </el-menu-item>

          <!-- 2. 主数据中心 -->
          <el-sub-menu v-if="hasMasterDataAccess" index="master-data">
            <template #title>
              <el-icon><Grid /></el-icon>
              <span>主数据中心</span>
            </template>
            <el-menu-item v-if="canReadDictionaries" index="/master-data/dictionaries">
              <el-icon><Collection /></el-icon>业务字典
            </el-menu-item>
            <el-menu-item v-if="canReadMaterials" index="/master-data/materials">
              <el-icon><Box /></el-icon>物料与材料台账
            </el-menu-item>
            <el-menu-item v-if="canReadEquipments" index="/master-data/equipments">
              <el-icon><Setting /></el-icon>设备资产台账
            </el-menu-item>
            <el-menu-item v-if="canReadProcesses" index="/master-data/processes">
              <el-icon><Operation /></el-icon>工艺字典
            </el-menu-item>
            <el-menu-item v-if="canReadLabor" index="/master-data/labor">
              <el-icon><User /></el-icon>人员岗位与费率
            </el-menu-item>
            <el-menu-item v-if="canReadEnergy" index="/master-data/energy">
              <el-icon><Lightning /></el-icon>能源与日历中心
            </el-menu-item>
          </el-sub-menu>

          <!-- 3. 工程建模 -->
          <el-sub-menu v-if="hasEngineeringAccess" index="engineering">
            <template #title>
              <el-icon><Edit /></el-icon>
              <span>工程建模中心</span>
            </template>
            <el-menu-item v-if="canReadProjects" index="/engineering/projects">
              <el-icon><FolderOpened /></el-icon>产品方案池
            </el-menu-item>
            <el-menu-item v-if="canReadWorkbench" index="/engineering/workbench">
              <el-icon><Connection /></el-icon>设计要素编排
            </el-menu-item>
          </el-sub-menu>

          <!-- 4. 成本仿真与决策 -->
          <el-sub-menu v-if="hasCostingAccess" index="costing">
            <template #title>
              <el-icon><Money /></el-icon>
              <span>成本仿真与决策</span>
            </template>
            <el-menu-item v-if="canReadFinancialBaselines" index="/costing/lcc-financial-baselines">
              <el-icon><Tickets /></el-icon>财务评估标准
            </el-menu-item>
            <el-menu-item v-if="canReadSnapshotCenter" index="/costing/snapshot-center">
              <el-icon><Document /></el-icon>产品快照中心
            </el-menu-item>
            <el-menu-item v-if="canReadDecisionCenter" index="/costing/decision-center">
              <el-icon><TrendCharts /></el-icon>仿真结果优选与决策
            </el-menu-item>
          </el-sub-menu>

          <!-- 5. 系统管理 -->
          <el-sub-menu v-if="authStore.hasSystemAccess" index="system">
            <template #title>
              <el-icon><Tools /></el-icon>
              <span>系统管理</span>
            </template>
            <el-menu-item v-if="authStore.hasPermissionScope('/system/users:read')" index="/system/users">
              <el-icon><Avatar /></el-icon>用户管理
            </el-menu-item>
            <el-menu-item v-if="authStore.hasPermissionScope('/system/dictionaries:read')" index="/system/dictionaries">
              <el-icon><Collection /></el-icon>数据字典
            </el-menu-item>
            <el-menu-item v-if="authStore.hasPermissionScope('/system/permissions:read')" index="/system/permissions">
              <el-icon><Operation /></el-icon>菜单权限
            </el-menu-item>
            <el-menu-item v-if="authStore.hasPermissionScope('/system/roles:read')" index="/system/roles">
              <el-icon><Key /></el-icon>角色权限
            </el-menu-item>
            <el-menu-item v-if="authStore.hasPermissionScope('/system/audit-logs:read')" index="/system/audit">
              <el-icon><List /></el-icon>审计日志
            </el-menu-item>
          </el-sub-menu>
        </el-menu>
      </el-scrollbar>

      <!-- 折叠按钮 -->
      <div
        class="collapse-btn flex items-center justify-center h-12 flex-shrink-0 border-t border-gray-700 cursor-pointer hover:bg-gray-800 transition-colors"
        @click="isCollapsed = !isCollapsed"
      >
        <el-icon :size="16" color="#6b7280">
          <DArrowLeft v-if="!isCollapsed" />
          <DArrowRight v-else />
        </el-icon>
      </div>
    </el-aside>

    <!-- ══════════════ 右侧主区域 ══════════════ -->
    <el-container class="flex flex-col overflow-hidden">
      <!-- 顶部 Header -->
      <el-header class="header-wrapper flex items-center justify-between flex-shrink-0 border-b border-gray-200 bg-white px-6">
        <!-- 面包屑 / 标题 -->
        <div class="flex items-center gap-2">
          <el-icon :size="16" class="text-gray-400"><Location /></el-icon>
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item v-if="currentMeta.module && moduleTitle && moduleTitle !== currentMeta.title">
              {{ moduleTitle }}
            </el-breadcrumb-item>
            <el-breadcrumb-item v-if="currentMeta.title">
              {{ currentMeta.title }}
            </el-breadcrumb-item>
          </el-breadcrumb>
        </div>

        <!-- 右侧用户区 -->
        <div class="flex items-center gap-4">
          <span class="text-xs text-gray-400">{{ currentDate }}</span>
          <el-divider direction="vertical" />
          <el-dropdown trigger="click" @command="handleCommand">
            <div class="flex items-center gap-2 cursor-pointer hover:text-indigo-600 transition-colors">
              <el-avatar :size="32" class="bg-indigo-600">
                <el-icon><UserFilled /></el-icon>
              </el-avatar>
              <span class="text-sm text-gray-700 font-medium">{{ displayName }}</span>
              <el-icon :size="12" class="text-gray-400"><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile" :icon="User">个人信息</el-dropdown-item>
                <el-dropdown-item divided command="logout" :icon="SwitchButton">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <!-- 主内容区 -->
      <el-main class="main-content bg-gray-50 overflow-auto">
        <router-view v-slot="{ Component, route }">
          <transition name="page-fade" mode="out-in">
            <component :is="Component" :key="route.fullPath" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import {
  DataAnalysis, Monitor, Grid, Collection, Box, Setting, Operation,
  User, Edit, FolderOpened, Connection, Money, Tickets, Document,
  Tools, Avatar, Key, List, Lightning, TrendCharts, DArrowLeft,
  DArrowRight, Location, UserFilled, ArrowDown, SwitchButton,
} from '@element-plus/icons-vue'
import { ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const displayName = computed(() => authStore.currentUser?.real_name ?? authStore.currentUser?.username ?? '管理员')

// 侧边栏折叠状态
const isCollapsed = ref(false)

const route = useRoute()

const currentPath = computed(() => route.path)
const currentMeta = computed(() => route.meta as Record<string, unknown>)

const canReadDictionaries = computed(() => authStore.hasPermissionScope('/master-data/dict-templates:read'))
const canReadMaterials = computed(() => authStore.hasPermissionScope('/master-data/materials:read'))
const canReadEquipments = computed(() => authStore.hasPermissionScope('/master-data/equipments:read'))
const canReadProcesses = computed(() => authStore.hasPermissionScope('/master-data/processes:read'))
const canReadLabor = computed(() => authStore.hasPermissionScope('/master-data/labor:read'))
const canReadEnergy = computed(() => authStore.hasPermissionScope('/master-data/energy:read'))

const canReadProjects = computed(() => authStore.hasPermissionScope('/engineering/projects:read'))
const canReadWorkbench = computed(() => authStore.hasPermissionScope('/engineering/bom-nodes:read'))

const canReadFinancialBaselines = computed(() => authStore.hasPermissionScope('/costing/lcc-financial-baselines:read'))
const canReadSnapshotCenter = computed(() => authStore.hasPermissionScope('/engineering/snapshots:read'))
const canReadDecisionCenter = computed(() => authStore.hasPermissionScope('/engineering/snapshots:read'))

const hasMasterDataAccess = computed(() => (
  canReadDictionaries.value
  || canReadMaterials.value
  || canReadEquipments.value
  || canReadProcesses.value
  || canReadLabor.value
  || canReadEnergy.value
))

const hasEngineeringAccess = computed(() => canReadProjects.value || canReadWorkbench.value)
const hasCostingAccess = computed(() => (
  canReadFinancialBaselines.value
  || canReadSnapshotCenter.value
  || canReadDecisionCenter.value
))

const moduleMap: Record<string, string> = {
  dashboard: '首页',
  'master-data': '主数据中心',
  engineering: '工程建模中心',
  costing: '成本仿真与决策',
  system: '系统管理',
}

const moduleTitle = computed(
  () => moduleMap[String(currentMeta.value?.module ?? '')] ?? '',
)

const currentDate = computed(() =>
  new Date().toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  }),
)

async function handleCommand(cmd: string) {
  if (cmd === 'logout') {
    await ElMessageBox.confirm('确定要退出登录吗？', '退出确认', {
      type: 'warning',
      confirmButtonText: '确定',
      cancelButtonText: '取消',
    })
    // TODO: 清除 token / store
    authStore.logout()
  }
}
</script>

<style scoped>
.app-layout {
  font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

.aside-wrapper {
  background-color: #111827;
}

.header-wrapper {
  height: 56px;
}

.main-content {
  padding: 20px 24px;
}

/* 菜单深色定制 */
:deep(.menu-custom .el-sub-menu__title:hover),
:deep(.menu-custom .el-menu-item:hover) {
  background-color: rgba(99, 102, 241, 0.1) !important;
  color: #818cf8 !important;
}

:deep(.menu-custom .el-menu-item.is-active) {
  background-color: rgba(99, 102, 241, 0.15) !important;
  color: #818cf8 !important;
  border-right: 3px solid #6366f1;
}

:deep(.menu-custom .el-sub-menu__title) {
  color: #9ca3af;
}

:deep(.menu-custom.el-menu--collapse .el-sub-menu__icon-arrow) {
  display: none;
}

/* 页面切换过渡 */
.page-fade-enter-active,
.page-fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.page-fade-enter-from {
  opacity: 0;
  transform: translateY(6px);
}
.page-fade-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

/* Logo 文字淡入淡出 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
