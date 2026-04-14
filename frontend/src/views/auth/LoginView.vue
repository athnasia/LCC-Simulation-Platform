<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-950">
    <!-- 背景网格装饰 -->
    <div class="absolute inset-0 bg-[linear-gradient(rgba(99,102,241,0.05)_1px,transparent_1px),linear-gradient(90deg,rgba(99,102,241,0.05)_1px,transparent_1px)] bg-[size:40px_40px] pointer-events-none" />

    <div class="relative w-full max-w-md px-4">
      <!-- 工业感标题区 -->
      <div class="text-center mb-8">
        <div class="inline-flex items-center justify-center w-14 h-14 rounded-xl bg-indigo-600 mb-4">
          <el-icon :size="28" color="#fff"><DataAnalysis /></el-icon>
        </div>
        <h1 class="text-2xl font-bold text-white tracking-wide">
          工业互联网 LCC 仿真平台
        </h1>
        <p class="text-sm text-gray-500 mt-1">Industrial IoT · LCC Simulation System</p>
      </div>

      <!-- 登录卡片 -->
      <el-card class="!bg-gray-900 !border-gray-700 !rounded-2xl shadow-2xl">
        <template #header>
          <div class="text-sm font-medium text-gray-400 tracking-wider uppercase">
            账户登录
          </div>
        </template>

        <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          label-position="top"
          size="large"
          @keyup.enter="handleLogin"
        >
          <el-form-item label="用户名" prop="username">
            <el-input
              v-model="form.username"
              placeholder="请输入用户名"
              :prefix-icon="User"
              autocomplete="username"
            />
          </el-form-item>

          <el-form-item label="密码" prop="password">
            <el-input
              v-model="form.password"
              :type="showPassword ? 'text' : 'password'"
              placeholder="请输入密码"
              :prefix-icon="Lock"
              autocomplete="current-password"
            >
              <template #suffix>
                <el-icon
                  class="cursor-pointer text-gray-400 hover:text-gray-200 transition-colors"
                  @click="showPassword = !showPassword"
                >
                  <View v-if="!showPassword" />
                  <Hide v-else />
                </el-icon>
              </template>
            </el-input>
          </el-form-item>

          <el-form-item class="mt-6">
            <el-button
              type="primary"
              class="w-full"
              :loading="loading"
              @click="handleLogin"
            >
              登 录
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>

      <p class="text-center text-xs text-gray-600 mt-6">
        &copy; 2026 工业互联网 LCC 仿真优化平台
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { User, Lock, View, Hide, DataAnalysis } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

const formRef = ref<FormInstance>()
const showPassword = ref(false)
const loading = ref(false)

const form = reactive({
  username: '',
  password: '',
})

const rules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function handleLogin() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await authStore.login(form.username, form.password)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
:deep(.el-card__header) {
  border-bottom: 1px solid rgb(55 65 81);
  padding: 16px 20px;
}
:deep(.el-card__body) {
  padding: 24px 20px;
}
:deep(.el-form-item__label) {
  color: rgb(156 163 175) !important;
  font-size: 13px;
}
:deep(.el-input__wrapper) {
  background-color: rgb(17 24 39) !important;
  box-shadow: 0 0 0 1px rgb(55 65 81) !important;
}
:deep(.el-input__wrapper:hover),
:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px rgb(99 102 241) !important;
}
:deep(.el-input__inner) {
  color: rgb(229 231 235) !important;
}
:deep(.el-input__inner::placeholder) {
  color: rgb(75 85 99) !important;
}
</style>
