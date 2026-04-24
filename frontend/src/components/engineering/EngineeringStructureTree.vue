<template>
  <div class="engineering-structure-tree" v-loading="loading">
    <div class="tree-toolbar">
      <span class="tree-title">{{ title }}</span>
      <slot name="toolbar" />
    </div>

    <el-input
      v-model="filterText"
      clearable
      :prefix-icon="Search"
      :placeholder="filterPlaceholder"
      class="tree-search"
    />

    <div class="tree-body">
      <el-tree
        v-if="nodes.length > 0"
        ref="treeRef"
        :data="nodes"
        :props="treeProps"
        node-key="key"
        default-expand-all
        highlight-current
        :current-node-key="currentNodeKey || undefined"
        :filter-node-method="filterNode"
        :empty-text="treeEmptyText"
        @node-click="handleNodeClick"
      >
        <template #default="{ node, data }">
          <div class="tree-node">
            <span class="node-label">
              <el-icon v-if="data.type === 'project'" class="node-icon project"><Folder /></el-icon>
              <el-icon v-else-if="data.type === 'product'" class="node-icon product"><Box /></el-icon>
              <el-icon v-else class="node-icon scheme"><Document /></el-icon>
              <span class="node-text">{{ node.label }}</span>
              <el-tag v-if="badgeMap[data.key] !== undefined" size="small" type="info" effect="plain">
                {{ badgeMap[data.key] }}
              </el-tag>
            </span>

            <span v-if="showManageActions" class="node-actions">
              <el-button
                v-if="data.type === 'project'"
                link
                size="small"
                @click.stop="emit('create-product', data)"
              >
                <el-icon><Plus /></el-icon>
                产品
              </el-button>
              <el-button
                v-if="data.type === 'product'"
                link
                size="small"
                @click.stop="emit('create-scheme', data)"
              >
                <el-icon><Plus /></el-icon>
                方案
              </el-button>
              <el-button link size="small" @click.stop="emit('edit', data)">
                <el-icon><Edit /></el-icon>
              </el-button>
              <el-button link size="small" type="danger" @click.stop="emit('delete', data)">
                <el-icon><Delete /></el-icon>
              </el-button>
            </span>
          </div>
        </template>
      </el-tree>

      <el-empty v-else :description="emptyDescription" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { Box, Delete, Document, Edit, Folder, Plus, Search } from '@element-plus/icons-vue'
import type { TreeInstance } from 'element-plus'
import type { EngineeringTreeNode } from '@/utils/engineeringStructureTree'

const props = withDefaults(defineProps<{
  nodes: EngineeringTreeNode[]
  title?: string
  loading?: boolean
  currentNodeKey?: string | null
  showManageActions?: boolean
  emptyDescription?: string
  filterPlaceholder?: string
  badgeMap?: Record<string, number>
}>(), {
  title: '项目结构',
  loading: false,
  currentNodeKey: null,
  showManageActions: false,
  emptyDescription: '暂无数据',
  filterPlaceholder: '搜索项目 / 产品 / 方案',
  badgeMap: () => ({}),
})

const emit = defineEmits<{
  (e: 'node-click', node: EngineeringTreeNode): void
  (e: 'create-product', node: EngineeringTreeNode): void
  (e: 'create-scheme', node: EngineeringTreeNode): void
  (e: 'edit', node: EngineeringTreeNode): void
  (e: 'delete', node: EngineeringTreeNode): void
}>()

const treeRef = ref<TreeInstance>()
const filterText = ref('')
const treeEmptyText = computed(() => (filterText.value.trim() ? '未匹配到项目 / 产品 / 方案' : '暂无可用结构节点'))
const treeProps = {
  children: 'children',
  label: 'label',
}

watch(filterText, (value) => {
  treeRef.value?.filter(value)
})

function filterNode(value: string, data: EngineeringTreeNode) {
  if (!value) {
    return true
  }
  return data.label.toLowerCase().includes(value.trim().toLowerCase())
}

function handleNodeClick(node: EngineeringTreeNode) {
  emit('node-click', node)
}
</script>

<style scoped>
.engineering-structure-tree {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.tree-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.tree-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.tree-search {
  flex-shrink: 0;
}

.tree-body {
  min-height: 0;
  flex: 1;
  overflow: auto;
}

.tree-node {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding-right: 8px;
}

.node-label {
  min-width: 0;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.node-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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
  display: inline-flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}
</style>