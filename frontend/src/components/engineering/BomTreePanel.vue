<template>
  <div class="bom-tree-panel">
    <!-- 面板标题 -->
    <div class="panel-header">
      <h3>BOM 结构树</h3>
      <el-button 
        type="primary" 
        size="small" 
        :disabled="!hasCurrentSchemeVersion"
        @click="handleAddRootNode"
      >
        新增根节点
      </el-button>
    </div>
    
    <!-- 树形结构 -->
    <div class="panel-body">
      <el-tree
        v-if="bomTree.length > 0"
        ref="treeRef"
        :data="bomTree"
        :props="treeProps"
        node-key="id"
        highlight-current
        :expand-on-click-node="false"
        :default-expand-all="true"
        @node-click="handleNodeClick"
      >
        <template #default="{ node, data }">
          <div class="tree-node">
            <div class="node-content">
              <!-- 状态小圆点 -->
              <span 
                class="status-dot" 
                :class="data.is_configured ? 'configured' : 'unconfigured'"
                :title="data.is_configured ? '已配置工艺' : '未配置工艺'"
              />
              
              <!-- 节点名称 -->
              <span class="node-name">{{ data.node_name }}</span>
              <span class="node-code">({{ data.code }})</span>
              
              <!-- 节点类型标签 -->
              <el-tag 
                v-if="data.node_type === 'ASSEMBLY'" 
                size="small" 
                type="info"
              >
                装配
              </el-tag>
            </div>
            
            <!-- 操作按钮 -->
            <div class="node-actions">
              <el-button 
                link 
                type="primary" 
                size="small"
                @click.stop="handleAddChild(data)"
              >
                新增子级
              </el-button>
              <el-button 
                link 
                type="primary" 
                size="small"
                @click.stop="handleEdit(data)"
              >
                编辑
              </el-button>
              <el-button 
                link 
                type="danger" 
                size="small"
                @click.stop="handleDelete(data)"
              >
                删除
              </el-button>
            </div>
          </div>
        </template>
      </el-tree>
      
      <!-- 空状态 -->
      <el-empty 
        v-else 
        description="暂无 BOM 数据，请先添加根节点"
        :image-size="120"
      />
    </div>
    
    <!-- 新增/编辑弹窗 -->
    <BomNodeDialog 
      v-model="dialogVisible"
      :mode="dialogMode"
      :data="currentNode"
      :parent-id="currentParentId"
      @success="handleDialogSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { ElTree } from 'element-plus'
import { useEngineeringStore } from '@/stores/engineering'
import type { BomNode, BomNodeTree } from '@/api/engineering'
import BomNodeDialog from './BomNodeDialog.vue'

const store = useEngineeringStore()

// 树形组件引用
const treeRef = ref<InstanceType<typeof ElTree>>()

// 树形配置
const treeProps = {
  children: 'children',
  label: 'node_name',
}

// 从 Store 获取状态
const bomTree = computed(() => store.bomTree)
const hasCurrentSchemeVersion = computed(() => store.hasCurrentSchemeVersion)
const selectedBomNode = computed(() => store.selectedBomNode)

// 弹窗相关
const dialogVisible = ref(false)
const dialogMode = ref<'create' | 'edit'>('create')
const currentNode = ref<BomNode | null>(null)
const currentParentId = ref<number | null>(null)

// 点击节点
function handleNodeClick(data: BomNodeTree) {
  store.selectBomNode(data)
}

// 新增根节点
function handleAddRootNode() {
  dialogMode.value = 'create'
  currentNode.value = null
  currentParentId.value = null
  dialogVisible.value = true
}

// 新增子级
function handleAddChild(node: BomNodeTree) {
  dialogMode.value = 'create'
  currentNode.value = null
  currentParentId.value = node.id
  dialogVisible.value = true
}

// 编辑节点
function handleEdit(node: BomNodeTree) {
  dialogMode.value = 'edit'
  currentNode.value = node
  currentParentId.value = null
  dialogVisible.value = true
}

// 删除节点
async function handleDelete(node: BomNodeTree) {
  try {
    await ElMessageBox.confirm(
      `确定要删除节点 [${node.node_name}] 吗？删除后不可恢复，子节点也会一并删除。`,
      '危险操作',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning',
        center: true,
      }
    )
    
    await store.deleteBomNode(node.id)
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') {
      console.error('Delete failed:', error)
    }
  }
}

// 弹窗成功回调
function handleDialogSuccess() {
  dialogVisible.value = false
}
</script>

<style scoped>
.bom-tree-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e4e7ed;
}

.panel-header h3 {
  margin: 0;
  font-size: 16px;
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
  padding: 4px 0;
}

.node-content {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.status-dot.configured {
  background-color: #67c23a;
}

.status-dot.unconfigured {
  background-color: #f56c6c;
}

.node-name {
  font-weight: 500;
  color: #303133;
}

.node-code {
  font-size: 12px;
  color: #909399;
}

.node-actions {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s;
}

.tree-node:hover .node-actions {
  opacity: 1;
}

:deep(.el-tree-node__content) {
  height: auto;
  padding: 4px 0;
}

:deep(.el-tree-node__content:hover) {
  background-color: #f5f7fa;
}

:deep(.el-tree-node.is-current > .el-tree-node__content) {
  background-color: #ecf5ff;
}
</style>
