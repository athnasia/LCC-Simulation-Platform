/**
 * 错误处理工具函数
 * 
 * 提供统一的错误处理和日志记录
 */

import { ElMessage, ElNotification } from 'element-plus'
import type { ApiError } from '@/types/common'

/**
 * 错误类型枚举
 */
export enum ErrorType {
  NETWORK = 'NETWORK',
  AUTH = 'AUTH',
  PERMISSION = 'PERMISSION',
  VALIDATION = 'VALIDATION',
  NOT_FOUND = 'NOT_FOUND',
  SERVER = 'SERVER',
  UNKNOWN = 'UNKNOWN',
}

/**
 * 错误信息映射
 */
const errorMessages: Record<string, string> = {
  NETWORK_ERROR: '网络连接失败，请检查网络设置',
  REQUEST_TIMEOUT: '请求超时，请稍后重试',
  UNAUTHORIZED: '登录已过期，请重新登录',
  FORBIDDEN: '您没有执行此操作的权限',
  NOT_FOUND: '请求的资源不存在',
  VALIDATION_ERROR: '输入数据验证失败',
  INTERNAL_SERVER_ERROR: '服务器内部错误，请稍后重试',
  SERVICE_UNAVAILABLE: '服务暂时不可用，请稍后重试',
}

/**
 * 解析错误类型
 */
export function parseErrorType(error: any): ErrorType {
  if (!error.response) {
    if (error.code === 'ECONNABORTED') return ErrorType.NETWORK
    return ErrorType.NETWORK
  }
  
  const status = error.response.status
  
  switch (status) {
    case 401:
      return ErrorType.AUTH
    case 403:
      return ErrorType.PERMISSION
    case 404:
      return ErrorType.NOT_FOUND
    case 422:
      return ErrorType.VALIDATION
    case 500:
    case 502:
    case 503:
    case 504:
      return ErrorType.SERVER
    default:
      return ErrorType.UNKNOWN
  }
}

/**
 * 获取错误消息
 */
export function getErrorMessage(error: any): string {
  if (typeof error === 'string') return error
  
  if (error.response?.data?.message) {
    return error.response.data.message
  }
  
  if (error.response?.data?.detail) {
    const detail = error.response.data.detail
    if (Array.isArray(detail)) {
      return detail.map((e: any) => e.msg).join('；')
    }
    if (typeof detail === 'string') {
      return detail
    }
  }
  
  const errorType = parseErrorType(error)
  return errorMessages[errorType] || error.message || '操作失败'
}

/**
 * 显示错误消息
 */
export function showError(error: any, duration = 5000): void {
  const message = getErrorMessage(error)
  const errorType = parseErrorType(error)
  
  if (errorType === ErrorType.AUTH) {
    ElNotification({
      title: '认证失败',
      message: '登录已过期，请重新登录',
      type: 'warning',
      duration,
    })
    localStorage.removeItem('access_token')
    window.location.href = '/login'
    return
  }
  
  if (errorType === ErrorType.PERMISSION) {
    ElMessage.warning(message || '您没有执行此操作的权限')
    return
  }
  
  ElMessage.error(message)
}

/**
 * 显示成功消息
 */
export function showSuccess(message: string): void {
  ElMessage.success(message)
}

/**
 * 显示警告消息
 */
export function showWarning(message: string): void {
  ElMessage.warning(message)
}

/**
 * 显示信息消息
 */
export function showInfo(message: string): void {
  ElMessage.info(message)
}

/**
 * 错误日志记录
 */
export function logError(error: any, context?: string): void {
  const errorInfo = {
    context,
    message: getErrorMessage(error),
    type: parseErrorType(error),
    timestamp: new Date().toISOString(),
    stack: error.stack,
    response: error.response?.data,
  }
  
  console.error('[Error Log]', errorInfo)
}

/**
 * 全局错误处理器
 */
export function setupGlobalErrorHandler(): void {
  window.addEventListener('unhandledrejection', (event) => {
    logError(event.reason, 'Unhandled Promise Rejection')
    showError(event.reason)
  })
  
  window.addEventListener('error', (event) => {
    logError(event.error, 'Uncaught Error')
    showError(event.error)
  })
}

/**
 * 创建错误处理函数
 */
export function createErrorHandler(context: string) {
  return (error: any) => {
    logError(error, context)
    showError(error)
    throw error
  }
}
