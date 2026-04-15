import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'
import router from '@/router'

interface LoginResponse {
  access_token: string
  token_type: string
}

interface CurrentUser {
  id: number
  username: string
  real_name: string
  is_active: boolean
  permission_scopes: string[]
  roles: Array<{
    id: number
    name: string
    code: string
    is_active: boolean
  }>
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('access_token'))
  const currentUser = ref<CurrentUser | null>(null)

  const isLoggedIn = computed(() => !!token.value)
  const isSuperAdmin = computed(() =>
    currentUser.value?.roles.some((role) => role.code === 'SUPER_ADMIN') ?? false,
  )

  const permissionScopes = computed(() => currentUser.value?.permission_scopes ?? [])

  function hasPermissionScope(scope: string) {
    return isSuperAdmin.value || permissionScopes.value.includes(scope)
  }

  const hasSystemAccess = computed(() => {
    return [
      '/system/users:read',
      '/system/permissions:read',
      '/system/roles:read',
      '/system/audit-logs:read',
      '/system/dictionaries:read',
    ].some((scope) => hasPermissionScope(scope))
  })

  function getFirstSystemRoute() {
    if (hasPermissionScope('/system/dictionaries:read')) {
      return '/system/dictionaries'
    }
    if (hasPermissionScope('/system/users:read')) {
      return '/system/users'
    }
    if (hasPermissionScope('/system/permissions:read')) {
      return '/system/permissions'
    }
    if (hasPermissionScope('/system/roles:read')) {
      return '/system/roles'
    }
    if (hasPermissionScope('/system/audit-logs:read')) {
      return '/system/audit'
    }
    return '/dashboard'
  }

  function clearAuthState() {
    token.value = null
    currentUser.value = null
    localStorage.removeItem('access_token')
  }

  async function login(username: string, password: string) {
    // 后端 LoginRequest 是 Pydantic JSON body，不是 OAuth2 form-data
    const res = await request.post<LoginResponse>('/auth/login', { username, password })

    token.value = res.data.access_token
    localStorage.setItem('access_token', res.data.access_token)
    ElMessage.success('登录成功')
    await fetchCurrentUser({ silent: false })
    router.push('/')
  }

  async function fetchCurrentUser(options: { silent?: boolean } = {}) {
    try {
      const res = await request.get<CurrentUser>('/auth/me')
      currentUser.value = res.data
      return true
    } catch {
      clearAuthState()
      if (!options.silent) {
        ElMessage.error('登录状态已失效，请重新登录')
        router.push('/login')
      }
      return false
    }
  }

  function logout() {
    clearAuthState()
    router.push('/login')
  }

  return {
    token,
    currentUser,
    isLoggedIn,
    isSuperAdmin,
    permissionScopes,
    hasPermissionScope,
    hasSystemAccess,
    getFirstSystemRoute,
    login,
    fetchCurrentUser,
    logout,
  }
})
