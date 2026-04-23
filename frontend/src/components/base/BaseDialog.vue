<template>
  <el-dialog
    v-model="visible"
    :title="dialogTitle"
    :width="width"
    :close-on-click-modal="closeOnClickModal"
    :close-on-press-escape="closeOnPressEscape"
    :destroy-on-close="destroyOnClose"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="modelValue"
      :rules="rules"
      :label-width="labelWidth"
      :label-position="labelPosition"
      :disabled="disabled"
    >
      <slot />
    </el-form>
    
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="handleCancel">{{ cancelText }}</el-button>
        <el-button v-if="showConfirm" type="primary" :loading="loading" @click="handleConfirm">
          {{ confirmText }}
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'

const props = withDefaults(defineProps<{
  modelValue: boolean
  mode?: 'create' | 'edit' | 'view'
  title?: string
  width?: string | number
  rules?: FormRules
  labelWidth?: string | number
  labelPosition?: 'left' | 'right' | 'top'
  disabled?: boolean
  loading?: boolean
  closeOnClickModal?: boolean
  closeOnPressEscape?: boolean
  destroyOnClose?: boolean
  showConfirm?: boolean
  confirmText?: string
  cancelText?: string
}>(), {
  mode: 'create',
  title: '',
  width: '500px',
  rules: () => ({}),
  labelWidth: '80px',
  labelPosition: 'right',
  disabled: false,
  loading: false,
  closeOnClickModal: false,
  closeOnPressEscape: true,
  destroyOnClose: true,
  showConfirm: true,
  confirmText: '确定',
  cancelText: '取消',
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'confirm': []
  'cancel': []
  'close': []
}>()

const formRef = ref<FormInstance>()

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
})

const dialogTitle = computed(() => {
  if (props.title) return props.title
  const modeTitles = {
    create: '新建',
    edit: '编辑',
    view: '查看',
  }
  return modeTitles[props.mode]
})

function handleClose() {
  formRef.value?.resetFields()
  emit('close')
}

function handleCancel() {
  visible.value = false
  emit('cancel')
}

async function handleConfirm() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (valid) {
    emit('confirm')
  }
}

defineExpose({
  formRef,
  validate: () => formRef.value?.validate(),
  resetFields: () => formRef.value?.resetFields(),
  clearValidate: () => formRef.value?.clearValidate(),
})
</script>
