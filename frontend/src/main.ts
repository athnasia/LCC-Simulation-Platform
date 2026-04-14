import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import { createPinia } from 'pinia'
import router from '@/router'
import { useAuthStore } from '@/stores/auth'
import App from './App.vue'
import './style.css'

const app = createApp(App)
const pinia = createPinia()

// 全量注册 Element Plus 图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(ElementPlus)
app.use(pinia)

const authStore = useAuthStore(pinia)

router.beforeEach(async (to) => {
  if (to.path === '/login') {
    if (authStore.token && !authStore.currentUser) {
      await authStore.fetchCurrentUser({ silent: true })
    }
    if (authStore.isLoggedIn) {
      return '/dashboard'
    }
    return true
  }

  if (!authStore.token) {
    return {
      path: '/login',
      query: { redirect: to.fullPath },
    }
  }

  if (!authStore.currentUser) {
    const ok = await authStore.fetchCurrentUser({ silent: true })
    if (!ok) {
      return {
        path: '/login',
        query: { redirect: to.fullPath },
      }
    }
  }

  if (to.matched.some((record) => record.meta.requiresSystemAccess) && !authStore.hasSystemAccess) {
    return '/dashboard'
  }

  const requiredPermissionScope = to.matched
    .map((record) => record.meta.requiredPermissionScope)
    .find((scope): scope is string => typeof scope === 'string')

  if (requiredPermissionScope && !authStore.hasPermissionScope(requiredPermissionScope)) {
    if (to.path.startsWith('/system')) {
      return authStore.getFirstSystemRoute()
    }
    return '/dashboard'
  }

  return true
})

app.use(router)

app.mount('#app')
