import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { ElMessage } from 'element-plus'
import router from '@/router'
import { authApi, type CurrentUser, type TokenResponse } from '@/api/auth'

const TOKEN_KEY = 'access_token'
const REFRESH_TOKEN_KEY = 'refresh_token'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem(TOKEN_KEY))
  const refreshToken = ref<string | null>(localStorage.getItem(REFRESH_TOKEN_KEY))
  const currentUser = ref<CurrentUser | null>(null)
  const isRefreshing = ref(false)

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
    refreshToken.value = null
    currentUser.value = null
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
  }

  function saveTokens(tokens: TokenResponse) {
    token.value = tokens.access_token
    refreshToken.value = tokens.refresh_token
    localStorage.setItem(TOKEN_KEY, tokens.access_token)
    localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token)
  }

  async function handleTokenRefresh(): Promise<boolean> {
    const storedRefreshToken = localStorage.getItem(REFRESH_TOKEN_KEY)
    if (!storedRefreshToken || isRefreshing.value) {
      return false
    }

    isRefreshing.value = true
    try {
      const res = await authApi.refresh({ refresh_token: storedRefreshToken })
      saveTokens(res.data)
      return true
    } catch {
      clearAuthState()
      ElMessage.error('登录已过期，请重新登录')
      router.push('/login')
      return false
    } finally {
      isRefreshing.value = false
    }
  }

  async function login(username: string, password: string) {
    const res = await authApi.login({ username, password })
    saveTokens(res.data)
    ElMessage.success('登录成功')
    await fetchCurrentUser({ silent: false })
    router.push('/')
  }

  async function fetchCurrentUser(options: { silent?: boolean } = {}) {
    try {
      const res = await authApi.me()
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
    refreshToken,
    currentUser,
    isRefreshing,
    isLoggedIn,
    isSuperAdmin,
    permissionScopes,
    hasPermissionScope,
    hasSystemAccess,
    getFirstSystemRoute,
    login,
    fetchCurrentUser,
    logout,
    handleTokenRefresh,
    saveTokens,
    clearAuthState,
  }
})
