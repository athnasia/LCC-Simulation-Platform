<template>
  <div class="projects-view">
    <div class="page-header">
      <h2>产品方案池</h2>
      <el-button type="primary" @click="handleCreateProject">
        <el-icon><Plus /></el-icon>
        新建项目
      </el-button>
    </div>
    
    <div class="page-content">
      <!-- 左侧：项目/产品/方案树 -->
      <div class="tree-panel">
        <div class="panel-header">
          <span>项目结构</span>
        </div>
        <div class="panel-body">
          <el-tree
            ref="treeRef"
            :data="treeData"
            :props="treeProps"
            node-key="id"
            :default-expand-all="true"
            :highlight-current="true"
            @node-click="handleNodeClick"
          >
            <template #default="{ node, data }">
              <div class="tree-node">
                <span class="node-label">
                  <el-icon v-if="data.type === 'project'" class="node-icon project"><Folder /></el-icon>
                  <el-icon v-else-if="data.type === 'product'" class="node-icon product"><Box /></el-icon>
                  <el-icon v-else-if="data.type === 'scheme'" class="node-icon scheme"><Document /></el-icon>
                  <span>{{ node.label }}</span>
                </span>
                <span class="node-actions">
                  <el-button
                    v-if="data.type === 'project'"
                    link
                    size="small"
                    @click.stop="handleCreateProduct(data)"
                  >
                    <el-icon><Plus /></el-icon>
                    产品
                  </el-button>
                  <el-button
                    v-if="data.type === 'product'"
                    link
                    size="small"
                    @click.stop="handleCreateScheme(data)"
                  >
                    <el-icon><Plus /></el-icon>
                    方案
                  </el-button>
                  <el-button
                    link
                    size="small"
                    @click.stop="handleEdit(data)"
                  >
                    <el-icon><Edit /></el-icon>
                  </el-button>
                  <el-button
                    link
                    size="small"
                    type="danger"
                    @click.stop="handleDelete(data)"
                  >
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </span>
              </div>
            </template>
          </el-tree>
          
          <el-empty v-if="treeData.length === 0" description="暂无项目，请点击右上角新建" />
        </div>
      </div>
      
      <!-- 右侧：详情与版本管理 -->
      <div class="detail-panel">
        <template v-if="selectedNode">
          <!-- 项目详情 -->
          <template v-if="selectedNode.type === 'project'">
            <div class="panel-header">
              <span>项目详情</span>
              <el-button type="primary" size="small" @click="handleCreateProduct(selectedNode)">
                <el-icon><Plus /></el-icon>
                新建产品
              </el-button>
            </div>
            <div class="panel-body">
              <el-descriptions :column="2" border>
                <el-descriptions-item label="项目名称">{{ selectedNode.data.name }}</el-descriptions-item>
                <el-descriptions-item label="项目编码">{{ selectedNode.data.code }}</el-descriptions-item>
                <el-descriptions-item label="状态">
                  <el-tag :type="selectedNode.data.is_active ? 'success' : 'info'">
                    {{ selectedNode.data.is_active ? '启用' : '停用' }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="创建时间">{{ selectedNode.data.created_at }}</el-descriptions-item>
                <el-descriptions-item label="描述" :span="2">{{ selectedNode.data.description || '-' }}</el-descriptions-item>
              </el-descriptions>
            </div>
          </template>
          
          <!-- 产品详情 -->
          <template v-else-if="selectedNode.type === 'product'">
            <div class="panel-header">
              <span>产品详情</span>
              <el-button type="primary" size="small" @click="handleCreateScheme(selectedNode)">
                <el-icon><Plus /></el-icon>
                新建方案
              </el-button>
            </div>
            <div class="panel-body">
              <el-descriptions :column="2" border>
                <el-descriptions-item label="产品名称">{{ selectedNode.data.name }}</el-descriptions-item>
                <el-descriptions-item label="产品编码">{{ selectedNode.data.code }}</el-descriptions-item>
                <el-descriptions-item label="所属项目">{{ selectedNode.data.project_name || '-' }}</el-descriptions-item>
                <el-descriptions-item label="状态">
                  <el-tag :type="selectedNode.data.is_active ? 'success' : 'info'">
                    {{ selectedNode.data.is_active ? '启用' : '停用' }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="创建时间">{{ selectedNode.data.created_at }}</el-descriptions-item>
                <el-descriptions-item label="描述">{{ selectedNode.data.description || '-' }}</el-descriptions-item>
              </el-descriptions>
            </div>
          </template>
          
          <!-- 方案详情与版本管理 -->
          <template v-else-if="selectedNode.type === 'scheme'">
            <div class="panel-header">
              <span>方案详情与版本管理</span>
              <el-button type="primary" size="small" @click="handleCreateVersion(selectedNode)">
                <el-icon><Plus /></el-icon>
                新建版本
              </el-button>
            </div>
            <div class="panel-body">
              <el-descriptions :column="2" border style="margin-bottom: 16px;">
                <el-descriptions-item label="方案名称">{{ selectedNode.data.name }}</el-descriptions-item>
                <el-descriptions-item label="方案编码">{{ selectedNode.data.code }}</el-descriptions-item>
                <el-descriptions-item label="所属产品">{{ selectedNode.data.product_name || '-' }}</el-descriptions-item>
                <el-descriptions-item label="状态">
                  <el-tag :type="selectedNode.data.is_active ? 'success' : 'info'">
                    {{ selectedNode.data.is_active ? '启用' : '停用' }}
                  </el-tag>
                </el-descriptions-item>
              </el-descriptions>
              
              <el-divider content-position="left">版本列表</el-divider>
              
              <el-table :data="versions" v-loading="versionsLoading" border>
                <el-table-column prop="version" label="版本号" width="80" />
                <el-table-column prop="status" label="状态" width="100">
                  <template #default="{ row }">
                    <el-tag :type="getVersionStatusType(row.status)">
                      {{ getVersionStatusText(row.status) }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="description" label="描述" />
                <el-table-column prop="released_at" label="发布时间" width="160" />
                <el-table-column label="操作" width="280" align="center">
                  <template #default="{ row }">
                    <el-button
                      v-if="row.status === 'DRAFT'"
                      link
                      type="primary"
                      @click="handleReleaseVersion(row)"
                    >
                      发布
                    </el-button>
                    <el-button
                      link
                      type="primary"
                      @click="handleOpenWorkbench(selectedNode.data.id, row.id, row.status)"
                    >
                      {{ row.status === 'RELEASED' ? '查看工作台' : '进入工作台' }}
                    </el-button>
                    <el-button
                      link
                      type="success"
                      @click="handleOpenSnapshots(selectedNode.data.id, row.id)"
                    >
                      快照与成本台账
                    </el-button>
                    <el-button
                      v-if="row.status === 'DRAFT'"
                      link
                      type="danger"
                      @click="handleDeleteVersion(row)"
                    >
                      删除
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </template>
        </template>
        
        <el-empty v-else description="请在左侧选择项目、产品或方案" />
      </div>
    </div>
    
    <!-- 项目对话框 -->
    <ProjectDialog
      v-model="projectDialogVisible"
      :project="editingProject"
      @success="handleDialogSuccess"
    />
    
    <!-- 产品对话框 -->
    <ProductDialog
      v-model="productDialogVisible"
      :product="editingProduct"
      :project-id="currentProjectId"
      @success="handleDialogSuccess"
    />
    
    <!-- 方案对话框 -->
    <SchemeDialog
      v-model="schemeDialogVisible"
      :scheme="editingScheme"
      :product-id="currentProductId"
      @success="handleDialogSuccess"
    />
    
    <!-- 版本对话框 -->
    <VersionDialog
      v-model="versionDialogVisible"
      :scheme-id="currentSchemeId"
      @success="handleVersionSuccess"
    />
    
    <!-- 快照选择对话框 -->
    <el-dialog
      v-model="snapshotDialogVisible"
      title="选择快照查看成本台账"
      width="600px"
      destroy-on-close
    >
      <el-table
        :data="snapshots"
        v-loading="snapshotsLoading"
        border
        stripe
        size="small"
      >
        <el-table-column prop="snapshot_code" label="快照编码" width="150" />
        <el-table-column prop="snapshot_name" label="快照名称" />
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 'READY' ? 'success' : 'info'" size="small">
              {{ row.status === 'READY' ? '就绪' : '草稿' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160" />
        <el-table-column label="操作" width="120" align="center">
          <template #default="{ row }">
            <el-button
              link
              type="primary"
              @click="handleViewCostLedger(row.id)"
            >
              查看成本台账
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, ElTree } from 'element-plus'
import { Plus, Edit, Delete, Folder, Box, Document } from '@element-plus/icons-vue'
import { projectApi, productApi, designSchemeApi, designSchemeVersionApi, modelSnapshotApi } from '@/api/engineering'
import ProjectDialog from '@/components/engineering/ProjectDialog.vue'
import ProductDialog from '@/components/engineering/ProductDialog.vue'
import SchemeDialog from '@/components/engineering/SchemeDialog.vue'
import VersionDialog from '@/components/engineering/VersionDialog.vue'

const router = useRouter()

interface TreeNode {
  id: number
  label: string
  type: 'project' | 'product' | 'scheme'
  data: any
  children?: TreeNode[]
}

const treeRef = ref<InstanceType<typeof ElTree>>()
const treeData = ref<TreeNode[]>([])
const treeProps = {
  children: 'children',
  label: 'label',
}

const selectedNode = ref<TreeNode | null>(null)
const versions = ref<any[]>([])
const versionsLoading = ref(false)

const projectDialogVisible = ref(false)
const productDialogVisible = ref(false)
const schemeDialogVisible = ref(false)
const versionDialogVisible = ref(false)
const snapshotDialogVisible = ref(false)

const snapshots = ref<any[]>([])
const snapshotsLoading = ref(false)
const currentVersionId = ref<number | null>(null)

const editingProject = ref<any>(null)
const editingProduct = ref<any>(null)
const editingScheme = ref<any>(null)

const currentProjectId = ref<number | null>(null)
const currentProductId = ref<number | null>(null)
const currentSchemeId = ref<number | null>(null)

const loading = ref(false)

async function loadTreeData() {
  loading.value = true
  try {
    const [projectsRes, productsRes, schemesRes] = await Promise.all([
      projectApi.list({ size: 100 }),
      productApi.list({ size: 100 }),
      designSchemeApi.list({ size: 100 }),
    ])
    
    const projects = projectsRes.data.items || []
    const products = productsRes.data.items || []
    const schemes = schemesRes.data.items || []
    
    const productMap = new Map(products.map((p: any) => [p.id, p]))
    const schemeMap = new Map(schemes.map((s: any) => [s.id, s]))
    
    const projectMap = new Map<number, TreeNode>()
    treeData.value = projects.map((project: any) => {
      const node: TreeNode = {
        id: project.id,
        label: project.name,
        type: 'project',
        data: project,
        children: [],
      }
      projectMap.set(project.id, node)
      return node
    })
    
    products.forEach((product: any) => {
      const projectNode = projectMap.get(product.project_id)
      if (projectNode) {
        if (!projectNode.children) projectNode.children = []
        projectNode.children.push({
          id: product.id,
          label: product.name,
          type: 'product',
          data: { ...product, project_name: projectMap.get(product.project_id)?.data.name },
          children: [],
        })
      }
    })
    
    const productNodeMap = new Map<number, TreeNode>()
    treeData.value.forEach((projectNode) => {
      projectNode.children?.forEach((productNode) => {
        productNodeMap.set(productNode.id, productNode)
      })
    })
    
    schemes.forEach((scheme: any) => {
      const productNode = productNodeMap.get(scheme.product_id)
      if (productNode) {
        if (!productNode.children) productNode.children = []
        productNode.children.push({
          id: scheme.id,
          label: scheme.name,
          type: 'scheme',
          data: { ...scheme, product_name: productNode.data.name },
        })
      }
    })
  } catch (error) {
    console.error('Failed to load tree data:', error)
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

async function loadVersions(schemeId: number) {
  versionsLoading.value = true
  try {
    const res = await designSchemeVersionApi.list({ scheme_id: schemeId, size: 100 })
    versions.value = res.data.items || []
  } catch (error) {
    console.error('Failed to load versions:', error)
    ElMessage.error('加载版本列表失败')
  } finally {
    versionsLoading.value = false
  }
}

function handleNodeClick(data: TreeNode) {
  selectedNode.value = data
  if (data.type === 'scheme') {
    loadVersions(data.id)
  }
}

function handleCreateProject() {
  editingProject.value = null
  projectDialogVisible.value = true
}

function handleCreateProduct(node: TreeNode) {
  currentProjectId.value = node.id
  editingProduct.value = null
  productDialogVisible.value = true
}

function handleCreateScheme(node: TreeNode) {
  currentProductId.value = node.id
  editingScheme.value = null
  schemeDialogVisible.value = true
}

function handleCreateVersion(node: TreeNode) {
  currentSchemeId.value = node.id
  versionDialogVisible.value = true
}

function handleEdit(node: TreeNode) {
  if (node.type === 'project') {
    editingProject.value = node.data
    projectDialogVisible.value = true
  } else if (node.type === 'product') {
    editingProduct.value = node.data
    productDialogVisible.value = true
  } else if (node.type === 'scheme') {
    editingScheme.value = node.data
    schemeDialogVisible.value = true
  }
}

async function handleDelete(node: TreeNode) {
  const typeNames = { project: '项目', product: '产品', scheme: '方案' }
  
  try {
    await ElMessageBox.confirm(`确定要删除该${typeNames[node.type]}吗？`, '确认删除', {
      type: 'warning',
    })
    
    if (node.type === 'project') {
      await projectApi.delete(node.id)
    } else if (node.type === 'product') {
      await productApi.delete(node.id)
    } else if (node.type === 'scheme') {
      await designSchemeApi.delete(node.id)
    }
    
    ElMessage.success('删除成功')
    loadTreeData()
    selectedNode.value = null
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Delete failed:', error)
      ElMessage.error('删除失败')
    }
  }
}

async function handleReleaseVersion(version: any) {
  try {
    await ElMessageBox.confirm('确定要发布该版本吗？发布后将无法修改。', '确认发布', {
      type: 'warning',
    })
    
    await designSchemeVersionApi.release(version.id)
    ElMessage.success('发布成功')
    loadVersions(selectedNode.value!.id)
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Release failed:', error)
      ElMessage.error('发布失败')
    }
  }
}

async function handleDeleteVersion(version: any) {
  try {
    await ElMessageBox.confirm('确定要删除该版本吗？', '确认删除', {
      type: 'warning',
    })
    
    await designSchemeVersionApi.delete(version.id)
    ElMessage.success('删除成功')
    loadVersions(selectedNode.value!.id)
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Delete failed:', error)
      ElMessage.error('删除失败')
    }
  }
}

function handleOpenWorkbench(schemeId: number, versionId: number, status: string) {
  const query: Record<string, any> = { schemeId, versionId }
  if (status === 'RELEASED') {
    query.readonly = 'true'
  }
  router.push({
    path: '/engineering/workbench',
    query,
  })
}

async function handleOpenSnapshots(schemeId: number, versionId: number) {
  currentVersionId.value = versionId
  snapshotsLoading.value = true
  snapshotDialogVisible.value = true
  
  try {
    const res = await modelSnapshotApi.list({ scheme_version_id: versionId, size: 100 })
    snapshots.value = res.data.items || []
    
    if (snapshots.value.length === 0) {
      ElMessage.warning('该版本暂无快照，请先生成快照')
      snapshotDialogVisible.value = false
    }
  } catch (error: any) {
    console.error('获取快照列表失败:', error)
    ElMessage.error(error.response?.data?.message || '获取快照列表失败')
    snapshotDialogVisible.value = false
  } finally {
    snapshotsLoading.value = false
  }
}

function handleViewCostLedger(snapshotId: number) {
  snapshotDialogVisible.value = false
  router.push(`/engineering/cost-ledger/${snapshotId}`)
}

function handleDialogSuccess() {
  loadTreeData()
}

function handleVersionSuccess() {
  if (selectedNode.value) {
    loadVersions(selectedNode.value.id)
  }
}

function getVersionStatusType(status: string) {
  const map: Record<string, string> = {
    DRAFT: 'info',
    RELEASED: 'success',
    ARCHIVED: 'warning',
  }
  return map[status] || 'info'
}

function getVersionStatusText(status: string) {
  const map: Record<string, string> = {
    DRAFT: '草稿',
    RELEASED: '已发布',
    ARCHIVED: '已归档',
  }
  return map[status] || status
}

onMounted(() => {
  loadTreeData()
})
</script>

<style scoped>
.projects-view {
  height: 100%;
  display: flex;
  flex-direction: column;
  background-color: #f5f7fa;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background-color: #fff;
  border-bottom: 1px solid #e4e7ed;
}

.page-header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.page-content {
  flex: 1;
  display: flex;
  overflow: hidden;
  padding: 16px;
  gap: 16px;
}

.tree-panel,
.detail-panel {
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.tree-panel {
  width: 350px;
  min-width: 300px;
}

.detail-panel {
  flex: 1;
  min-width: 500px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #e4e7ed;
  font-weight: 600;
  color: #303133;
}

.panel-body {
  flex: 1;
  overflow: auto;
  padding: 16px;
}

.tree-node {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding-right: 8px;
}

.node-label {
  display: flex;
  align-items: center;
  gap: 6px;
}

.node-icon {
  font-size: 16px;
}

.node-icon.project {
  color: #409eff;
}

.node-icon.product {
  color: #67c23a;
}

.node-icon.scheme {
  color: #e6a23c;
}

.node-actions {
  display: flex;
  gap: 4px;
}
</style>
