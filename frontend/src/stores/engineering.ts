import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { ElMessage } from 'element-plus'
import type {
  Project,
  Product,
  DesignScheme,
  DesignSchemeVersion,
  BomNode,
  BomNodeTree,
  ComponentProcessRoute,
  RouteStepBind,
  RouteStepBindWithProcess,
  ModelSnapshot,
  GenerateSnapshotRequest,
  GenerateSnapshotResponse,
} from '@/api/engineering'
import {
  projectApi,
  productApi,
  designSchemeApi,
  designSchemeVersionApi,
  bomNodeApi,
  componentProcessRouteApi,
  routeStepBindApi,
  modelSnapshotApi,
} from '@/api/engineering'

export const useEngineeringStore = defineStore('engineering', () => {
  // ═══════════════════════════════════════════════════════════════════════════════
  // 状态定义
  // ═══════════════════════════════════════════════════════════════════════════════

  // 列表数据
  const projects = ref<Project[]>([])
  const products = ref<Product[]>([])
  const schemes = ref<DesignScheme[]>([])

  // 当前选中的项目、产品、方案、版本
  const currentProject = ref<Project | null>(null)
  const currentProduct = ref<Product | null>(null)
  const currentScheme = ref<DesignScheme | null>(null)
  const currentSchemeVersion = ref<DesignSchemeVersion | null>(null)

  // BOM 树相关状态
  const bomTree = ref<BomNodeTree[]>([])
  const selectedBomNode = ref<BomNode | null>(null)
  const bomTreeLoading = ref(false)

  // 工艺路线相关状态
  const processRoutes = ref<ComponentProcessRoute[]>([])
  const selectedRoute = ref<ComponentProcessRoute | null>(null)
  const routeSteps = ref<RouteStepBindWithProcess[]>([])
  const selectedStep = ref<RouteStepBindWithProcess | null>(null)
  const routesLoading = ref(false)
  const stepsLoading = ref(false)

  // 快照相关状态
  const snapshots = ref<ModelSnapshot[]>([])
  const currentSnapshot = ref<ModelSnapshot | null>(null)
  const snapshotsLoading = ref(false)

  // 版本列表
  const schemeVersions = ref<DesignSchemeVersion[]>([])

  // ═══════════════════════════════════════════════════════════════════════════════
  // 辅助函数
  // ═══════════════════════════════════════════════════════════════════════════════

  /**
   * 递归检查所有叶子节点是否已配置工艺路线
   * @param nodes BOM 节点树
   * @returns 是否所有叶子节点都已配置
   */
  function checkAllLeafNodesConfigured(nodes: BomNodeTree[]): boolean {
    for (const node of nodes) {
      // 如果是叶子节点（没有子节点或子节点为空）
      if (!node.children || node.children.length === 0) {
        // 如果叶子节点未配置，返回 false
        if (!node.is_configured) {
          return false
        }
      } else {
        // 如果是装配节点（有子节点），递归检查子节点
        if (!checkAllLeafNodesConfigured(node.children)) {
          return false
        }
      }
    }
    return true
  }

  /**
   * 统计叶子节点数量
   * @param nodes BOM 节点树
   * @returns 叶子节点总数
   */
  function countLeafNodes(nodes: BomNodeTree[]): number {
    let count = 0
    for (const node of nodes) {
      if (!node.children || node.children.length === 0) {
        count++
      } else {
        count += countLeafNodes(node.children)
      }
    }
    return count
  }

  /**
   * 统计已配置的叶子节点数量
   * @param nodes BOM 节点树
   * @returns 已配置的叶子节点数量
   */
  function countConfiguredLeafNodes(nodes: BomNodeTree[]): number {
    let count = 0
    for (const node of nodes) {
      if (!node.children || node.children.length === 0) {
        if (node.is_configured) {
          count++
        }
      } else {
        count += countConfiguredLeafNodes(node.children)
      }
    }
    return count
  }

  // ═══════════════════════════════════════════════════════════════════════════════
  // 计算属性
  // ═══════════════════════════════════════════════════════════════════════════════

  const hasSelectedBomNode = computed(() => !!selectedBomNode.value)
  const hasSelectedRoute = computed(() => !!selectedRoute.value)
  const hasCurrentSchemeVersion = computed(() => !!currentSchemeVersion.value)
  const isCurrentVersionEditable = computed(() => {
    const status = currentSchemeVersion.value?.status
    return !!currentSchemeVersion.value && status !== 'RELEASED' && status !== 'ARCHIVED'
  })

  // 当前 BOM 节点是否已配置工艺路线
  const isCurrentNodeConfigured = computed(() => {
    return selectedBomNode.value?.is_configured ?? false
  })

  // 所有叶子节点是否都已配置工艺路线
  const isAllLeafNodesConfigured = computed(() => {
    if (bomTree.value.length === 0) {
      return false
    }
    return checkAllLeafNodesConfigured(bomTree.value)
  })

  // 叶子节点配置统计
  const leafNodeStats = computed(() => {
    const total = countLeafNodes(bomTree.value)
    const configured = countConfiguredLeafNodes(bomTree.value)
    return {
      total,
      configured,
      unconfigured: total - configured,
      percentage: total > 0 ? Math.round((configured / total) * 100) : 0,
    }
  })

  // 当前方案版本是否可以生成快照
  const canGenerateSnapshot = computed(() => {
    return hasCurrentSchemeVersion.value && bomTree.value.length > 0 && isAllLeafNodesConfigured.value
  })

  function ensureCurrentVersionEditable(action: string): boolean {
    if (!currentSchemeVersion.value) {
      ElMessage.warning('请先选择方案版本')
      return false
    }

    if (isCurrentVersionEditable.value) {
      return true
    }

    ElMessage.warning(
      `当前版本 V${currentSchemeVersion.value.version} 已发布或归档，不能${action}。请先创建新的草稿版本。`,
    )
    return false
  }

  // ═══════════════════════════════════════════════════════════════════════════════
  // Actions - 项目管理
  // ═══════════════════════════════════════════════════════════════════════════════

  async function loadProjects() {
    try {
      const res = await projectApi.list({ size: 100, is_active: true })
      projects.value = res.data.items || []
    } catch (error) {
      console.error('Failed to load projects:', error)
      ElMessage.error('加载项目列表失败')
    }
  }

  async function loadProject(projectId: number) {
    try {
      const res = await projectApi.detail(projectId)
      currentProject.value = res.data
    } catch (error) {
      console.error('Failed to load project:', error)
      ElMessage.error('加载项目失败')
    }
  }

  // ═══════════════════════════════════════════════════════════════════════════════
  // Actions - 产品管理
  // ═══════════════════════════════════════════════════════════════════════════════

  async function loadProducts(projectId: number) {
    try {
      const res = await productApi.list({ project_id: projectId, size: 100, is_active: true })
      products.value = res.data.items || []
    } catch (error) {
      console.error('Failed to load products:', error)
      ElMessage.error('加载产品列表失败')
    }
  }

  async function loadProduct(productId: number) {
    try {
      const res = await productApi.detail(productId)
      currentProduct.value = res.data
      return res.data
    } catch (error) {
      console.error('Failed to load product:', error)
      ElMessage.error('加载产品失败')
      return null
    }
  }

  // ═══════════════════════════════════════════════════════════════════════════════
  // Actions - 设计方案管理
  // ═══════════════════════════════════════════════════════════════════════════════

  async function loadSchemes(productId: number) {
    try {
      const res = await designSchemeApi.list({ product_id: productId, size: 100, is_active: true })
      schemes.value = res.data.items || []
    } catch (error) {
      console.error('Failed to load schemes:', error)
      ElMessage.error('加载方案列表失败')
    }
  }

  async function loadScheme(schemeId: number) {
    try {
      const res = await designSchemeApi.detail(schemeId)
      currentScheme.value = res.data
      return res.data
    } catch (error) {
      console.error('Failed to load scheme:', error)
      ElMessage.error('加载设计方案失败')
      return null
    }
  }

  // ═══════════════════════════════════════════════════════════════════════════════
  // Actions - 版本管理
  // ═══════════════════════════════════════════════════════════════════════════════

  async function loadSchemeVersions(schemeId: number) {
    try {
      const res = await designSchemeVersionApi.list({ scheme_id: schemeId, size: 100 })
      schemeVersions.value = res.data.items || []
    } catch (error) {
      console.error('Failed to load scheme versions:', error)
      ElMessage.error('加载版本列表失败')
    }
  }

  async function switchSchemeVersion(versionId: number) {
    try {
      const res = await designSchemeVersionApi.detail(versionId)
      currentSchemeVersion.value = res.data

      processRoutes.value = []
      selectedBomNode.value = null
      selectedRoute.value = null
      routeSteps.value = []
      selectedStep.value = null
      
      // 切换版本后，重新加载 BOM 树
      await loadBomTree(versionId)
    } catch (error) {
      console.error('Failed to switch version:', error)
      ElMessage.error('切换版本失败')
    }
  }

  // ═══════════════════════════════════════════════════════════════════════════════
  // Actions - BOM 树管理
  // ═══════════════════════════════════════════════════════════════════════════════

  async function loadBomTree(schemeVersionId: number) {
    bomTreeLoading.value = true
    try {
      const res = await bomNodeApi.getTree(schemeVersionId)
      bomTree.value = res.data
    } catch (error) {
      console.error('Failed to load BOM tree:', error)
      ElMessage.error('加载 BOM 树失败')
    } finally {
      bomTreeLoading.value = false
    }
  }

  async function selectBomNode(node: BomNode) {
    selectedBomNode.value = node
    selectedRoute.value = null
    routeSteps.value = []
    selectedStep.value = null
    
    // 选中节点后，加载该节点的工艺路线
    await loadProcessRoutes(node.id)
  }

  async function createBomNode(data: Partial<BomNode>) {
    if (!ensureCurrentVersionEditable('新增 BOM 节点')) {
      return
    }

    try {
      const res = await bomNodeApi.create({
        ...data,
        scheme_version_id: currentSchemeVersion.value.id,
      } as BomNode)
      
      ElMessage.success('创建节点成功')
      
      // 重新加载 BOM 树
      await loadBomTree(currentSchemeVersion.value.id)
      
      return res.data
    } catch (error) {
      console.error('Failed to create BOM node:', error)
      ElMessage.error('创建节点失败')
    }
  }

  async function updateBomNode(nodeId: number, data: Partial<BomNode>) {
    if (!ensureCurrentVersionEditable('修改 BOM 节点')) {
      return
    }

    try {
      const res = await bomNodeApi.update(nodeId, data)
      
      ElMessage.success('更新节点成功')
      
      // 重新加载 BOM 树
      if (currentSchemeVersion.value) {
        await loadBomTree(currentSchemeVersion.value.id)
      }
      
      return res.data
    } catch (error) {
      console.error('Failed to update BOM node:', error)
      ElMessage.error('更新节点失败')
    }
  }

  async function deleteBomNode(nodeId: number) {
    if (!ensureCurrentVersionEditable('删除 BOM 节点')) {
      return
    }

    try {
      await bomNodeApi.remove(nodeId)
      
      ElMessage.success('删除节点成功')
      
      // 重新加载 BOM 树
      if (currentSchemeVersion.value) {
        await loadBomTree(currentSchemeVersion.value.id)
      }
      
      // 如果删除的是当前选中的节点，清空选中状态
      if (selectedBomNode.value?.id === nodeId) {
        selectedBomNode.value = null
        processRoutes.value = []
        selectedRoute.value = null
        routeSteps.value = []
        selectedStep.value = null
      }
    } catch (error) {
      console.error('Failed to delete BOM node:', error)
      ElMessage.error('删除节点失败')
    }
  }

  // ═══════════════════════════════════════════════════════════════════════════════
  // Actions - 工艺路线管理
  // ═══════════════════════════════════════════════════════════════════════════════

  async function loadProcessRoutes(bomNodeId: number) {
    routesLoading.value = true
    try {
      const res = await componentProcessRouteApi.list({ bom_node_id: bomNodeId, size: 100 })
      processRoutes.value = res.data.items || []

      selectedRoute.value = null
      routeSteps.value = []
      selectedStep.value = null
    } catch (error) {
      console.error('Failed to load process routes:', error)
      ElMessage.error('加载工艺路线失败')
    } finally {
      routesLoading.value = false
    }
  }

  async function selectRoute(route: ComponentProcessRoute) {
    selectedRoute.value = route
    
    // 选中路线后，加载该路线的步骤
    await loadRouteSteps(route.id)
  }

  async function createProcessRoute(data: Partial<ComponentProcessRoute>) {
    if (!ensureCurrentVersionEditable('新增工艺路线')) {
      return
    }

    if (!selectedBomNode.value) {
      ElMessage.warning('请先选择 BOM 节点')
      return
    }

    try {
      const res = await componentProcessRouteApi.create({
        ...data,
        bom_node_id: selectedBomNode.value.id,
      } as ComponentProcessRoute)
      
      ElMessage.success('创建工艺路线成功')
      
      // 重新加载工艺路线列表
      await loadProcessRoutes(selectedBomNode.value.id)
      
      // 更新 BOM 节点的配置状态
      await updateBomNode(selectedBomNode.value.id, { is_configured: true })
      
      return res.data
    } catch (error) {
      console.error('Failed to create process route:', error)
      ElMessage.error('创建工艺路线失败')
    }
  }

  async function deleteProcessRoute(routeId: number) {
    if (!ensureCurrentVersionEditable('删除工艺路线')) {
      return
    }

    try {
      await componentProcessRouteApi.remove(routeId)
      
      ElMessage.success('删除工艺路线成功')
      
      // 重新加载工艺路线列表
      if (selectedBomNode.value) {
        await loadProcessRoutes(selectedBomNode.value.id)
      }
    } catch (error) {
      console.error('Failed to delete process route:', error)
      ElMessage.error('删除工艺路线失败')
    }
  }

  // ═══════════════════════════════════════════════════════════════════════════════
  // Actions - 路线步骤管理
  // ═══════════════════════════════════════════════════════════════════════════════

  async function loadRouteSteps(routeId: number) {
    stepsLoading.value = true
    try {
      const res = await routeStepBindApi.listWithProcess(routeId)
      routeSteps.value = res.data
      selectedStep.value = null
    } catch (error) {
      console.error('Failed to load route steps:', error)
      ElMessage.error('加载路线步骤失败')
    } finally {
      stepsLoading.value = false
    }
  }

  function selectStep(step: RouteStepBindWithProcess | null) {
    selectedStep.value = step
  }

  async function addRouteStep(processId: number) {
    if (!ensureCurrentVersionEditable('新增工序步骤')) {
      return
    }

    if (!selectedRoute.value) {
      ElMessage.warning('请先选择工艺路线')
      return
    }

    try {
      const nextOrder = routeSteps.value.length + 1
      
      const res = await routeStepBindApi.create({
        route_id: selectedRoute.value.id,
        process_id: processId,
        step_order: nextOrder,
      })
      
      ElMessage.success('添加工序成功')
      
      // 重新加载路线步骤
      await loadRouteSteps(selectedRoute.value.id)
      
      return res.data
    } catch (error) {
      console.error('Failed to add route step:', error)
      ElMessage.error('添加工序失败')
    }
  }

  async function addFirstProcessWithDefaultRoute(processId: number) {
    if (!ensureCurrentVersionEditable('新增工序步骤')) {
      return
    }

    if (!selectedBomNode.value) {
      ElMessage.warning('请先选择 BOM 节点')
      return
    }

    try {
      const defaultRouteName = `${selectedBomNode.value.node_name}_默认路线`
      const defaultRouteCode = `R_${selectedBomNode.value.code}_${Date.now()}`
      
      const createRes = await componentProcessRouteApi.create({
        bom_node_id: selectedBomNode.value.id,
        route_name: defaultRouteName,
        route_code: defaultRouteCode,
        description: '系统自动创建的默认工艺路线',
      } as ComponentProcessRoute)
      
      const newRoute = createRes.data
      selectedRoute.value = newRoute
      
      const nextOrder = 1
      await routeStepBindApi.create({
        route_id: newRoute.id,
        process_id: processId,
        step_order: nextOrder,
      })
      
      ElMessage.success('添加首道工序成功')
      
      await loadProcessRoutes(selectedBomNode.value.id)
      
      await updateBomNode(selectedBomNode.value.id, { is_configured: true })
      
      return newRoute
    } catch (error) {
      console.error('Failed to add first process with default route:', error)
      ElMessage.error('添加首道工序失败')
    }
  }

  async function updateRouteStep(stepId: number, data: Partial<RouteStepBind>) {
    if (!ensureCurrentVersionEditable('修改资源参数覆写')) {
      return
    }

    try {
      const res = await routeStepBindApi.update(stepId, data)
      
      ElMessage.success('更新工序成功')
      
      // 重新加载路线步骤
      if (selectedRoute.value) {
        await loadRouteSteps(selectedRoute.value.id)
      }
      
      return res.data
    } catch (error) {
      console.error('Failed to update route step:', error)
      ElMessage.error('更新工序失败')
    }
  }

  async function deleteRouteStep(stepId: number) {
    if (!ensureCurrentVersionEditable('删除工序步骤')) {
      return
    }

    try {
      await routeStepBindApi.remove(stepId)
      
      ElMessage.success('删除工序成功')
      
      // 重新加载路线步骤
      if (selectedRoute.value) {
        await loadRouteSteps(selectedRoute.value.id)
      }
    } catch (error) {
      console.error('Failed to delete route step:', error)
      ElMessage.error('删除工序失败')
    }
  }

  async function reorderRouteSteps(stepIds: number[]) {
    if (!ensureCurrentVersionEditable('调整工序顺序')) {
      return
    }

    if (!selectedRoute.value) {
      return
    }

    try {
      await routeStepBindApi.reorder(selectedRoute.value.id, stepIds)
      
      ElMessage.success('调整顺序成功')
      
      // 重新加载路线步骤
      await loadRouteSteps(selectedRoute.value.id)
    } catch (error) {
      console.error('Failed to reorder route steps:', error)
      ElMessage.error('调整顺序失败')
    }
  }

  // ═══════════════════════════════════════════════════════════════════════════════
  // Actions - 快照管理
  // ═══════════════════════════════════════════════════════════════════════════════

  async function loadSnapshots(schemeVersionId: number) {
    snapshotsLoading.value = true
    try {
      const res = await modelSnapshotApi.list({ scheme_version_id: schemeVersionId, size: 100 })
      snapshots.value = res.data.items || []
    } catch (error) {
      console.error('Failed to load snapshots:', error)
      ElMessage.error('加载快照列表失败')
    } finally {
      snapshotsLoading.value = false
    }
  }

  async function generateSnapshot(data: GenerateSnapshotRequest): Promise<GenerateSnapshotResponse | null> {
    // 前置校验：检查是否所有叶子节点都已配置
    if (!isAllLeafNodesConfigured.value) {
      const stats = leafNodeStats.value
      ElMessage.error(
        `还有 ${stats.unconfigured} 个零件未配置工艺路线，无法生成快照。当前进度：${stats.configured}/${stats.total}`
      )
      return null
    }

    try {
      const res = await modelSnapshotApi.generate(data)
      
      ElMessage.success('生成快照成功')
      
      // 重新加载快照列表
      await loadSnapshots(data.scheme_version_id)
      
      return res.data
    } catch (error) {
      console.error('Failed to generate snapshot:', error)
      ElMessage.error('生成快照失败')
      return null
    }
  }

  async function loadSnapshot(snapshotId: number) {
    try {
      const res = await modelSnapshotApi.detail(snapshotId)
      currentSnapshot.value = res.data
    } catch (error) {
      console.error('Failed to load snapshot:', error)
      ElMessage.error('加载快照失败')
    }
  }

  // ═══════════════════════════════════════════════════════════════════════════════
  // Actions - 重置状态
  // ═══════════════════════════════════════════════════════════════════════════════

  function resetState() {
    currentProject.value = null
    currentProduct.value = null
    currentScheme.value = null
    currentSchemeVersion.value = null
    bomTree.value = []
    selectedBomNode.value = null
    processRoutes.value = []
    selectedRoute.value = null
    routeSteps.value = []
    selectedStep.value = null
    snapshots.value = []
    currentSnapshot.value = null
    schemeVersions.value = []
  }

  return {
    // 状态
    projects,
    products,
    schemes,
    currentProject,
    currentProduct,
    currentScheme,
    currentSchemeVersion,
    bomTree,
    selectedBomNode,
    bomTreeLoading,
    processRoutes,
    selectedRoute,
    routeSteps,
    selectedStep,
    routesLoading,
    stepsLoading,
    snapshots,
    currentSnapshot,
    snapshotsLoading,
    schemeVersions,

    // 计算属性
    hasSelectedBomNode,
    hasSelectedRoute,
    hasCurrentSchemeVersion,
    isCurrentVersionEditable,
    isCurrentNodeConfigured,
    isAllLeafNodesConfigured,
    leafNodeStats,
    canGenerateSnapshot,

    // Actions
    loadProjects,
    loadProject,
    loadProducts,
    loadProduct,
    loadSchemes,
    loadScheme,
    loadSchemeVersions,
    switchSchemeVersion,
    loadBomTree,
    selectBomNode,
    createBomNode,
    updateBomNode,
    deleteBomNode,
    loadProcessRoutes,
    selectRoute,
    createProcessRoute,
    deleteProcessRoute,
    loadRouteSteps,
    selectStep,
    addRouteStep,
    addFirstProcessWithDefaultRoute,
    updateRouteStep,
    deleteRouteStep,
    reorderRouteSteps,
    loadSnapshots,
    generateSnapshot,
    loadSnapshot,
    resetState,
  }
})
