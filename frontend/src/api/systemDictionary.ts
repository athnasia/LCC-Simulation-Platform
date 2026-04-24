import request from '@/utils/request'
import type { AxiosResponse } from 'axios'

export const ResourceType = {
  MATERIAL: 'MATERIAL',
  EQUIPMENT: 'EQUIPMENT',
  LABOR: 'LABOR',
  TOOL: 'TOOL',
  PROCESS: 'PROCESS',
} as const

export type ResourceType = (typeof ResourceType)[keyof typeof ResourceType]

export interface PageResult<T> {
  items: T[]
  total: number
  page: number
  size: number
  pages: number
}

export interface DictionaryType {
  id: number
  name: string
  code: string
  description: string | null
  sort_order: number
  is_active: boolean
  created_at: string
  updated_at: string
  created_by: string | null
  updated_by: string | null
}

export interface DictionaryItem {
  id: number
  dict_type_id: number
  value: string
  label: string
  description: string | null
  sort_order: number
  is_active: boolean
  extra_json: Record<string, unknown> | null
  created_at: string
  updated_at: string
  created_by: string | null
  updated_by: string | null
  dict_type: Pick<DictionaryType, 'id' | 'name' | 'code' | 'sort_order' | 'is_active'>
}

export interface DictionaryTypeQuery {
  keyword?: string
  is_active?: boolean
  page?: number
  size?: number
}

export interface DictionaryItemQuery {
  dict_type_id?: number
  dict_type_code?: string
  keyword?: string
  is_active?: boolean
  page?: number
  size?: number
}

export interface DictionaryTypeCreate {
  name: string
  code: string
  description?: string | null
  sort_order?: number
  is_active?: boolean
}

export interface DictionaryTypeUpdate {
  name?: string
  description?: string | null
  sort_order?: number
  is_active?: boolean
}

export interface DictionaryItemCreate {
  dict_type_id: number
  value: string
  label: string
  description?: string | null
  sort_order?: number
  is_active?: boolean
  extra_json?: Record<string, unknown> | null
}

export interface DictionaryItemUpdate {
  label?: string
  description?: string | null
  sort_order?: number
  is_active?: boolean
  extra_json?: Record<string, unknown> | null
}

export interface DictionaryCacheItem {
  value: string
  label: string
  sort_order: number
  extra_json: Record<string, unknown> | null
}

export interface DictionaryCacheType {
  name: string
  code: string
  items: DictionaryCacheItem[]
}

export interface DictionaryCacheResponse {
  dictionaries: DictionaryCacheType[]
}

export interface ResourceCategory {
  id: number
  name: string
  code: string
  resource_type: ResourceType
  parent_id: number | null
  sort_order: number
  is_active: boolean
  description: string | null
  created_at: string
  updated_at: string
  created_by: string | null
  updated_by: string | null
}

export interface ResourceCategoryQuery {
  keyword?: string
  resource_type?: ResourceType
  parent_id?: number
  is_active?: boolean
  page?: number
  size?: number
}

export interface ResourceCategoryCreate {
  name: string
  code: string
  resource_type: ResourceType
  parent_id?: number | null
  sort_order?: number
  is_active?: boolean
  description?: string | null
}

export type ResourceCategoryUpdate = Partial<ResourceCategoryCreate>

export const systemDictionaryApi = {
  listTypes: (params: DictionaryTypeQuery): Promise<AxiosResponse<PageResult<DictionaryType>>> =>
    request.get('/system/dictionaries/types', { params }),

  createType: (data: DictionaryTypeCreate): Promise<AxiosResponse<DictionaryType>> =>
    request.post('/system/dictionaries/types', data),

  detailType: (id: number): Promise<AxiosResponse<DictionaryType>> =>
    request.get(`/system/dictionaries/types/${id}`),

  updateType: (id: number, data: DictionaryTypeUpdate): Promise<AxiosResponse<DictionaryType>> =>
    request.put(`/system/dictionaries/types/${id}`, data),

  removeType: (id: number): Promise<AxiosResponse<void>> =>
    request.delete(`/system/dictionaries/types/${id}`),

  listItems: (params: DictionaryItemQuery): Promise<AxiosResponse<PageResult<DictionaryItem>>> =>
    request.get('/system/dictionaries/items', { params }),

  createItem: (data: DictionaryItemCreate): Promise<AxiosResponse<DictionaryItem>> =>
    request.post('/system/dictionaries/items', data),

  detailItem: (id: number): Promise<AxiosResponse<DictionaryItem>> =>
    request.get(`/system/dictionaries/items/${id}`),

  updateItem: (id: number, data: DictionaryItemUpdate): Promise<AxiosResponse<DictionaryItem>> =>
    request.put(`/system/dictionaries/items/${id}`, data),

  removeItem: (id: number): Promise<AxiosResponse<void>> =>
    request.delete(`/system/dictionaries/items/${id}`),

  listResourceCategories: (params: ResourceCategoryQuery): Promise<AxiosResponse<PageResult<ResourceCategory>>> =>
    request.get('/system/dictionaries/resource-categories', { params }),

  createResourceCategory: (data: ResourceCategoryCreate): Promise<AxiosResponse<ResourceCategory>> =>
    request.post('/system/dictionaries/resource-categories', data),

  detailResourceCategory: (id: number): Promise<AxiosResponse<ResourceCategory>> =>
    request.get(`/system/dictionaries/resource-categories/${id}`),

  updateResourceCategory: (id: number, data: ResourceCategoryUpdate): Promise<AxiosResponse<ResourceCategory>> =>
    request.put(`/system/dictionaries/resource-categories/${id}`, data),

  removeResourceCategory: (id: number): Promise<AxiosResponse<void>> =>
    request.delete(`/system/dictionaries/resource-categories/${id}`),

  getCache: (): Promise<AxiosResponse<DictionaryCacheResponse>> =>
    request.get('/system/dictionaries/cache'),
}