import axios from 'axios'
import type { AxiosInstance, AxiosResponse, InternalAxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'

const request: AxiosInstance = axios.create({
  baseURL: '/api/v1',
  timeout: 15000,
})

// ── 请求拦截：注入 Authorization Token ──────────────────
request.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('access_token')
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

// ── 响应拦截：统一错误提示 ───────────────────────────────
request.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error) => {
    const status = error.response?.status
    // FastAPI 422 返回 { detail: [{loc,msg,type}] }，其他错误返回 { message } 或直接字符串
    const detail = error.response?.data?.detail
    let msg: string
    if (Array.isArray(detail) && detail.length > 0) {
      // Pydantic 校验错误：拼接所有字段的错误信息
      msg = detail.map((e: { msg: string }) => e.msg).join('；')
    } else if (typeof detail === 'string') {
      msg = detail
    } else {
      msg = error.response?.data?.message ?? error.message ?? '请求失败'
    }

    if (status === 401) {
      ElMessage.error('登录已过期，请重新登录')
      localStorage.removeItem('access_token')
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
