<template>
  <el-dialog
    v-model="visible"
    :title="dialogTitle"
    width="600px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="100px"
      label-position="right"
    >
      <el-form-item label="节点名称" prop="node_name">
        <el-input 
          v-model="form.node_name" 
          placeholder="请输入节点名称"
          maxlength="100"
          show-word-limit
        />
      </el-form-item>
      
      <el-form-item label="节点编码" prop="code">
        <el-input 
          v-model="form.code" 
          placeholder="请输入节点编码"
          maxlength="50"
          show-word-limit
          :disabled="mode === 'edit'"
        />
      </el-form-item>
      
      <el-form-item label="节点类型" prop="node_type">
        <el-radio-group v-model="form.node_type">
          <el-radio value="PART">零件</el-radio>
          <el-radio value="ASSEMBLY">装配</el-radio>
        </el-radio-group>
      </el-form-item>
      
      <el-form-item label="数量" prop="quantity">
        <el-input-number 
          v-model="form.quantity"
          :min="0"
          :precision="4"
          :step="1"
          placeholder="请输入数量"
          style="width: 100%"
        />
      </el-form-item>
      
      <el-form-item label="描述" prop="description">
        <el-input 
          v-model="form.description"
          type="textarea"
          :rows="3"
          placeholder="请输入描述"
          maxlength="512"
          show-word-limit
        />
      </el-form-item>
      
      <!-- 柔性属性：动态键值对 -->
      <el-divider content-position="left">
        <el-text type="info">柔性扩展属性</el-text>
      </el-divider>
      
      <div class="dynamic-attributes">
        <div 
          v-for="(attr, index) in dynamicAttributes" 
          :key="index"
          class="attribute-item"
        >
          <el-input 
            v-model="attr.key"
            placeholder="属性名（如：length）"
            style="width: 180px"
          />
          <span class="separator">:</span>
          <el-input 
            v-model="attr.value"
            placeholder="属性值（如：500）"
            style="flex: 1"
          />
          <el-button 
            link 
            type="danger"
            @click="removeAttribute(index)"
          >
            删除
          </el-button>
        </div>
        
        <el-button 
          type="primary" 
          link
          @click="addAttribute"
        >
          + 添加属性
        </el-button>
      </div>
    </el-form>
    
    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="handleSubmit">
        确定
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { useEngineeringStore } from '@/stores/engineering'
import type { BomNode } from '@/api/engineering'

interface Props {
  modelValue: boolean
  mode: 'create' | 'edit'
  data: BomNode | null
  parentId: number | null
}

interface DynamicAttribute {
  key: string
  value: string
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'success': []
}>()

const store = useEngineeringStore()

// 弹窗可见性
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})

// 弹窗标题
const dialogTitle = computed(() => {
  return props.mode === 'create' ? '新增 BOM 节点' : '编辑 BOM 节点'
})

// 表单引用
const formRef = ref<FormInstance>()
const submitting = ref(false)

// 表单数据
const form = ref({
  node_name: '',
  code: '',
  node_type: 'PART',
  quantity: null as number | null,
  description: '',
})

// 动态属性列表
const dynamicAttributes = ref<DynamicAttribute[]>([])

// 表单验证规则
const rules: FormRules = {
  node_name: [
    { required: true, message: '请输入节点名称', trigger: 'blur' },
    { min: 1, max: 100, message: '长度在 1 到 100 个字符', trigger: 'blur' },
  ],
  code: [
    { required: true, message: '请输入节点编码', trigger: 'blur' },
    { min: 1, max: 50, message: '长度在 1 到 50 个字符', trigger: 'blur' },
    { pattern: /^[A-Za-z0-9_-]+$/, message: '只能包含字母、数字、下划线和横杠', trigger: 'blur' },
  ],
  node_type: [
    { required: true, message: '请选择节点类型', trigger: 'change' },
  ],
}

// 监听弹窗打开
watch(visible, (newVal) => {
  if (newVal) {
    if (props.mode === 'edit' && props.data) {
      // 编辑模式：填充数据
      form.value = {
        node_name: props.data.node_name,
        code: props.data.code,
        node_type: props.data.node_type,
        quantity: props.data.quantity,
        description: props.data.description || '',
      }
      
      // 填充动态属性
      if (props.data.attributes) {
        dynamicAttributes.value = Object.entries(props.data.attributes).map(([key, value]) => ({
          key,
          value: String(value),
        }))
      } else {
        dynamicAttributes.value = []
      }
    } else {
      // 新增模式：重置表单
      form.value = {
        node_name: '',
        code: '',
        node_type: 'PART',
        quantity: null,
        description: '',
      }
      dynamicAttributes.value = []
    }
  }
})

// 添加动态属性
function addAttribute() {
  dynamicAttributes.value.push({
    key: '',
    value: '',
  })
}

// 删除动态属性
function removeAttribute(index: number) {
  dynamicAttributes.value.splice(index, 1)
}

// 将动态属性转换为 JSON 对象
function buildAttributesJson(): Record<string, any> | null {
  const validAttrs = dynamicAttributes.value.filter(attr => attr.key.trim() !== '')
  
  if (validAttrs.length === 0) {
    return null
  }
  
  const result: Record<string, any> = {}
  validAttrs.forEach(attr => {
    // 尝试将值转换为数字，如果失败则保留为字符串
    const numValue = Number(attr.value)
    result[attr.key.trim()] = isNaN(numValue) ? attr.value.trim() : numValue
  })
  
  return result
}

// 提交表单
async function handleSubmit() {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    
    submitting.value = true
    
    const attributes = buildAttributesJson()
    
    if (props.mode === 'create') {
      // 新增模式
      await store.createBomNode({
        node_name: form.value.node_name,
        code: form.value.code,
        node_type: form.value.node_type,
        quantity: form.value.quantity,
        description: form.value.description || null,
        attributes: attributes,
        parent_id: props.parentId,
      })
    } else if (props.data) {
      // 编辑模式
      await store.updateBomNode(props.data.id, {
        node_name: form.value.node_name,
        node_type: form.value.node_type,
        quantity: form.value.quantity,
        description: form.value.description || null,
        attributes: attributes,
      })
    }
    
    emit('success')
  } catch (error) {
    console.error('Submit failed:', error)
  } finally {
    submitting.value = false
  }
}

// 关闭弹窗
function handleClose() {
  visible.value = false
  formRef.value?.resetFields()
  dynamicAttributes.value = []
}
</script>

<style scoped>
.dynamic-attributes {
  padding: 0 20px;
}

.attribute-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.separator {
  color: #909399;
  font-weight: 500;
}

:deep(.el-divider__text) {
  background-color: #fff;
  padding: 0 10px;
}
</style>
