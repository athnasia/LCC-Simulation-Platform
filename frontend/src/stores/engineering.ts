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
  const routesLoading = ref(false)
  const stepsLoading = ref(false)

  // 快照相关状态
  const snapshots = ref<ModelSnapshot[]>([])
  const currentSnapshot = ref<ModelSnapshot | null>(null)
  const snapshotsLoading = ref(false)

  // 版本列表
  const schemeVersions = ref<DesignSchemeVersion[]>([])

  // ═══════════════════════════════════════════════════════════════════════════════
  // 计算属性
  // ═══════════════════════════════════════════════════════════════════════════════

  const hasSelectedBomNode = computed(() => !!selectedBomNode.value)
  const hasSelectedRoute = computed(() => !!selectedRoute.value)
  const hasCurrentSchemeVersion = computed(() => !!currentSchemeVersion.value)

  // 当前 BOM 节点是否已配置工艺路线
  const isCurrentNodeConfigured = computed(() => {
    return selectedBomNode.value?.is_configured ?? false
  })

  // 当前方案版本是否可以生成快照
  const canGenerateSnapshot = computed(() => {
    return hasCurrentSchemeVersion.value && bomTree.value.length > 0
  })

  // ═══════════════════════════════════════════════════════════════════════════════
  // Actions - 项目管理
  // ═══════════════════════════════════════════════════════════════════════════════

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

  async function loadProduct(productId: number) {
    try {
      const res = await productApi.detail(productId)
      currentProduct.value = res.data
    } catch (error) {
      console.error('Failed to load product:', error)
      ElMessage.error('加载产品失败')
    }
  }

  // ═══════════════════════════════════════════════════════════════════════════════
  // Actions - 设计方案管理
  // ═══════════════════════════════════════════════════════════════════════════════

  async function loadScheme(schemeId: number) {
    try {
      const res = await designSchemeApi.detail(schemeId)
      currentScheme.value = res.data
    } catch (error) {
      console.error('Failed to load scheme:', error)
      ElMessage.error('加载设计方案失败')
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
      
      // 切换版本后，重新加载 BOM 树
      await loadBomTree(versionId)
      
      // 清空选中的节点和路线
      selectedBomNode.value = null
      selectedRoute.value = null
      routeSteps.value = []
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
    
    // 选中节点后，加载该节点的工艺路线
    await loadProcessRoutes(node.id)
  }

  async function createBomNode(data: Partial<BomNode>) {
    if (!currentSchemeVersion.value) {
      ElMessage.warning('请先选择方案版本')
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
        selectedRoute.value = null
        routeSteps.value = []
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
      
      // 如果有路线，默认选中第一条
      if (processRoutes.value.length > 0) {
        await selectRoute(processRoutes.value[0])
      } else {
        selectedRoute.value = null
        routeSteps.value = []
      }
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
    } catch (error) {
      console.error('Failed to load route steps:', error)
      ElMessage.error('加载路线步骤失败')
    } finally {
      stepsLoading.value = false
    }
  }

  async function addRouteStep(processId: number) {
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

  async function updateRouteStep(stepId: number, data: Partial<RouteStepBind>) {
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
    snapshots.value = []
    currentSnapshot.value = null
    schemeVersions.value = []
  }

  return {
    // 状态
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
    isCurrentNodeConfigured,
    canGenerateSnapshot,

    // Actions
    loadProject,
    loadProduct,
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
    addRouteStep,
    updateRouteStep,
    deleteRouteStep,
    reorderRouteSteps,
    loadSnapshots,
    generateSnapshot,
    loadSnapshot,
    resetState,
  }
})
