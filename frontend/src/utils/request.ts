import axios from 'axios'
import type { AxiosInstance, AxiosResponse, InternalAxiosRequestConfig, AxiosError } from 'axios'
import { ElMessage } from 'element-plus'

const TOKEN_KEY = 'access_token'
const REFRESH_TOKEN_KEY = 'refresh_token'

const request: AxiosInstance = axios.create({
  baseURL: '/api/v1',
  timeout: 15000,
})

let isRefreshing = false
let failedQueue: Array<{
  resolve: (token: string) => void
  reject: (error: Error) => void
}> = []

function processQueue(error: Error | null, token: string | null) {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error)
    } else if (token) {
      prom.resolve(token)
    }
  })
  failedQueue = []
}

async function refreshToken(): Promise<string | null> {
  const storedRefreshToken = localStorage.getItem(REFRESH_TOKEN_KEY)
  if (!storedRefreshToken) {
    return null
  }

  try {
    const response = await axios.post('/api/v1/auth/refresh', {
      refresh_token: storedRefreshToken,
    })
    const { access_token, refresh_token: newRefreshToken } = response.data
    localStorage.setItem(TOKEN_KEY, access_token)
    localStorage.setItem(REFRESH_TOKEN_KEY, newRefreshToken)
    return access_token
  } catch {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
    return null
  }
}

request.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem(TOKEN_KEY)
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    if (config.method?.toLowerCase() === 'get') {
      config.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
      config.headers.Pragma = 'no-cache'
      config.headers.Expires = '0'
      config.params = {
        ...(config.params ?? {}),
        _t: Date.now(),
      }
    }

    return config
  },
  (error) => Promise.reject(error),
)

request.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (originalRequest.url === '/auth/refresh') {
        ElMessage.error('登录已过期，请重新登录')
        localStorage.removeItem(TOKEN_KEY)
        localStorage.removeItem(REFRESH_TOKEN_KEY)
        window.location.href = '/login'
        return Promise.reject(error)
      }

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`
            return request(originalRequest)
          })
          .catch((err) => Promise.reject(err))
      }

      originalRequest._retry = true
      isRefreshing = true

      try {
        const newToken = await refreshToken()
        if (newToken) {
          originalRequest.headers.Authorization = `Bearer ${newToken}`
          processQueue(null, newToken)
          return request(originalRequest)
        } else {
          processQueue(new Error('Token refresh failed'), null)
          ElMessage.error('登录已过期，请重新登录')
          window.location.href = '/login'
          return Promise.reject(error)
        }
      } catch (refreshError) {
        processQueue(refreshError as Error, null)
        ElMessage.error('登录已过期，请重新登录')
        window.location.href = '/login'
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    const status = error.response?.status
    const detail = (error.response?.data as { detail?: unknown })?.detail
    let msg: string
    if (Array.isArray(detail) && detail.length > 0) {
      msg = (detail as Array<{ msg: string }>).map((e) => e.msg).join('；')
    } else if (typeof detail === 'string') {
      msg = detail
    } else {
      msg = (error.response?.data as { message?: string })?.message ?? error.message ?? '请求失败'
    }

    if (status === 401) {
      ElMessage.error('登录已过期，请重新登录')
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(REFRESH_TOKEN_KEY)
      window.location.href = '/login'
    } else if (status === 403) {
      ElMessage.error(msg || '您没有执行此操作的权限')
    } else if (status === 404) {
      ElMessage.error('所请求的资源不存在')
    } else if (status === 422) {
      ElMessage.error(`输入校验失败：${msg}`)
    } else {
      ElMessage.error(msg)
    }

    return Promise.reject(error)
  },
)

export default request
