/**
 * API 请求工具函数
 * 
 * 提供类型安全的 API 调用方法
 */

import request from './request'
import type { AxiosResponse } from 'axios'
import type { PageResult, PageQuery, ApiResponse, ApiError } from '@/types/common'

/**
 * 创建分页查询参数
 */
export function createPageParams(params: PageQuery): Record<string, unknown> {
  return {
    keyword: params.keyword || '',
    page: params.page || 1,
    size: params.size || 20,
  }
}

/**
 * 通用 CRUD API 工厂函数
 */
export function createCrudApi<T, Q extends PageQuery, C, U = Partial<C>>(baseUrl: string) {
  return {
    list: (params?: Q): Promise<AxiosResponse<PageResult<T>>> => 
      request.get<PageResult<T>>(baseUrl, { params }),
    
    detail: (id: number): Promise<AxiosResponse<T>> => 
      request.get<T>(`${baseUrl}/${id}`),
    
    create: (data: C): Promise<AxiosResponse<T>> => 
      request.post<T>(baseUrl, data),
    
    update: (id: number, data: U): Promise<AxiosResponse<T>> => 
      request.put<T>(`${baseUrl}/${id}`, data),
    
    delete: (id: number): Promise<AxiosResponse<void>> => 
      request.delete<void>(`${baseUrl}/${id}`),
    
    batchDelete: (ids: number[]): Promise<AxiosResponse<void>> => 
      request.post<void>(`${baseUrl}/batch-delete`, { ids }),
  }
}

/**
 * 带重试的请求
 */
export async function requestWithRetry<T>(
  fn: () => Promise<AxiosResponse<T>>,
  maxRetries = 3,
  delay = 1000
): Promise<AxiosResponse<T>> {
  let lastError: Error | null = null
  
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn()
    } catch (error: any) {
      lastError = error
      if (error.response?.status === 401 || error.response?.status === 403) {
        throw error
      }
      if (i < maxRetries - 1) {
        await new Promise(resolve => setTimeout(resolve, delay * (i + 1)))
      }
    }
  }
  
  throw lastError
}

/**
 * 并发请求
 */
export async function parallelRequests<T extends Record<string, () => Promise<AxiosResponse<any>>>>(
  requests: T
): Promise<{ [K in keyof T]: T[K] extends () => Promise<AxiosResponse<infer R>> ? R : never }> {
  const keys = Object.keys(requests) as (keyof T)[]
  const promises = keys.map(key => requests[key]())
  const results = await Promise.all(promises)
  
  return keys.reduce((acc, key, index) => {
    acc[key] = results[index].data
    return acc
  }, {} as any)
}

/**
 * 请求取消器
 */
export class RequestCanceller {
  private controllers = new Map<string, AbortController>()
  
  create(key: string): AbortController {
    this.cancel(key)
    const controller = new AbortController()
    this.controllers.set(key, controller)
    return controller
  }
  
  cancel(key: string): void {
    const controller = this.controllers.get(key)
    if (controller) {
      controller.abort()
      this.controllers.delete(key)
    }
  }
  
  cancelAll(): void {
    this.controllers.forEach(controller => controller.abort())
    this.controllers.clear()
  }
}

/**
 * 错误处理装饰器
 */
export function withErrorHandler<T extends (...args: any[]) => Promise<any>>(
  fn: T,
  errorHandler?: (error: ApiError) => void
): T {
  return (async (...args: Parameters<T>) => {
    try {
      return await fn(...args)
    } catch (error: any) {
      const apiError: ApiError = {
        code: error.response?.data?.code || 'UNKNOWN_ERROR',
        message: error.response?.data?.message || error.message || '请求失败',
        detail: error.response?.data?.detail,
      }
      
      if (errorHandler) {
        errorHandler(apiError)
      } else {
        console.error('API Error:', apiError)
      }
      
      throw apiError
    }
  }) as T
}

export { request }
