import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/LoginView.vue'),
    meta: { title: '登录' },
  },
  {
    path: '/',
    name: 'Layout',
    component: () => import('@/layouts/AppLayout.vue'),
    redirect: '/dashboard',
    children: [
      // ── 模块一：全景视界 ──────────────────────────────
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/DashboardView.vue'),
        meta: { title: '全景视界', module: 'dashboard' },
      },

      // ── 模块二：主数据与资源中心 ─────────────────────
      {
        path: 'master-data',
        name: 'MasterData',
        component: () => import('@/layouts/RouteSectionView.vue'),
        redirect: '/master-data/dictionaries',
        meta: { title: '主数据中心', module: 'master-data' },
        children: [
          {
            path: 'dictionaries',
            name: 'Dictionaries',
            component: () => import('@/views/master-data/DictionariesView.vue'),
            meta: { title: '基础字典与模板', requiredPermissionScope: '/master-data/dictionaries:read' },
          },
          {
            path: 'materials',
            name: 'Materials',
            component: () => import('@/views/master-data/MaterialsView.vue'),
            meta: { title: '材料台账', requiredPermissionScope: '/master-data/materials:read' },
          },
          {
            path: 'equipments',
            name: 'Equipments',
            component: () => import('@/views/master-data/EquipmentsView.vue'),
            meta: { title: '设备能力库', requiredPermissionScope: '/master-data/equipments:read' },
          },
          {
            path: 'processes',
            name: 'Processes',
            component: () => import('@/views/master-data/ProcessesView.vue'),
            meta: { title: '工艺工时库', requiredPermissionScope: '/master-data/processes:read' },
          },
          {
            path: 'labor',
            name: 'Labor',
            component: () => import('@/views/master-data/LaborView.vue'),
            meta: { title: '人员技能矩阵', requiredPermissionScope: '/master-data/labor:read' },
          },
          {
            path: 'energy',
            name: 'Energy',
            component: () => import('@/views/master-data/EnergyView.vue'),
            meta: { title: '能源日历', requiredPermissionScope: '/master-data/energy:read' },
          },
        ],
      },

      // ── 模块三：工程建模与协同 ────────────────────────
      {
        path: 'engineering',
        name: 'Engineering',
        component: () => import('@/layouts/RouteSectionView.vue'),
        redirect: '/engineering/projects',
        meta: { title: '工程建模', module: 'engineering' },
        children: [
          {
            path: 'projects',
            name: 'Projects',
            component: () => import('@/views/engineering/ProjectsView.vue'),
            meta: { title: '产品方案池' },
          },
          {
            path: 'modeling',
            name: 'Modeling',
            component: () => import('@/views/engineering/ModelingView.vue'),
            meta: { title: '设计要素编排' },
          },
        ],
      },

      // ── 模块四：成本核算 ─────────────────────────────
      {
        path: 'costing',
        name: 'Costing',
        component: () => import('@/layouts/RouteSectionView.vue'),
        redirect: '/costing/rules',
        meta: { title: '成本核算', module: 'costing' },
        children: [
          {
            path: 'rules',
            name: 'CostingRules',
            component: () => import('@/views/costing/RulesView.vue'),
            meta: { title: '作业成本规则配置' },
          },
          {
            path: 'ledger',
            name: 'CostingLedger',
            component: () => import('@/views/costing/LedgerView.vue'),
            meta: { title: '静态产品成本台账' },
          },
        ],
      },

      // ── 模块五：仿真优化 ─────────────────────────────
      {
        path: 'simulation',
        name: 'Simulation',
        component: () => import('@/layouts/RouteSectionView.vue'),
        redirect: '/simulation/tasks',
        meta: { title: '仿真优化', module: 'simulation' },
        children: [
          {
            path: 'tasks',
            name: 'SimulationTasks',
            component: () => import('@/views/simulation/TasksView.vue'),
            meta: { title: 'LCC 仿真任务' },
          },
          {
            path: 'results',
            name: 'SimulationResults',
            component: () => import('@/views/simulation/ResultsView.vue'),
            meta: { title: '结果对比分析' },
          },
        ],
      },

      // ── 模块六：系统与平台管理 ────────────────────────
      {
        path: 'system',
        name: 'System',
        component: () => import('@/layouts/RouteSectionView.vue'),
        redirect: '/system/users',
        meta: { title: '系统管理', module: 'system', requiresSystemAccess: true },
        children: [
          {
            path: 'dictionaries',
            name: 'SystemDictionaries',
            component: () => import('@/views/system/DictionariesView.vue'),
            meta: { title: '数据字典', requiredPermissionScope: '/system/dictionaries:read' },
          },
          {
            path: 'users',
            name: 'Users',
            component: () => import('@/views/system/UsersView.vue'),
            meta: { title: '用户管理', requiredPermissionScope: '/system/users:read' },
          },
          {
            path: 'permissions',
            name: 'Permissions',
            component: () => import('@/views/system/PermissionsView.vue'),
            meta: { title: '菜单权限', requiredPermissionScope: '/system/permissions:read' },
          },
          {
            path: 'roles',
            name: 'Roles',
            component: () => import('@/views/system/RolesView.vue'),
            meta: { title: '角色权限', requiredPermissionScope: '/system/roles:read' },
          },
          {
            path: 'audit',
            name: 'Audit',
            component: () => import('@/views/system/AuditView.vue'),
            meta: { title: '审计日志', requiredPermissionScope: '/system/audit-logs:read' },
          },
        ],
      },
    ],
  },
  // 兜底重定向
  {
    path: '/:pathMatch(.*)*',
    redirect: '/dashboard',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
