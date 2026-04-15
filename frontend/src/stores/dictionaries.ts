import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { systemDictionaryApi } from '@/api/systemDictionary'
import type { DictionaryCacheItem, DictionaryCacheResponse, DictionaryCacheType } from '@/api/systemDictionary'

export interface DictionaryOption {
  label: string
  value: string
  sort_order: number
  extra_json: Record<string, unknown> | null
}

interface DictionaryCacheState {
  fetchedAt: number
  dictionaries: DictionaryCacheType[]
}

const STORAGE_KEY = 'system_dictionary_cache'
const CACHE_TTL_MS = 1000 * 60 * 60 * 12

export const useDictionaryStore = defineStore('dictionaries', () => {
  const dictionaries = ref<Record<string, DictionaryOption[]>>({})
  const fetchedAt = ref<number>(0)
  const loading = ref(false)

  const isLoaded = computed(() => Object.keys(dictionaries.value).length > 0)
  const isExpired = computed(() => {
    if (!fetchedAt.value) {
      return true
    }
    return Date.now() - fetchedAt.value > CACHE_TTL_MS
  })

  function normalizeCache(data: DictionaryCacheResponse): Record<string, DictionaryOption[]> {
    const result: Record<string, DictionaryOption[]> = {}
    for (const dictType of data.dictionaries) {
      result[dictType.code] = [...dictType.items]
        .sort((left, right) => left.sort_order - right.sort_order)
        .map((item: DictionaryCacheItem) => ({
          label: item.label,
          value: item.value,
          sort_order: item.sort_order,
          extra_json: item.extra_json,
        }))
    }
    return result
  }

  function persistCache() {
    const payload: DictionaryCacheState = {
      fetchedAt: fetchedAt.value,
      dictionaries: Object.entries(dictionaries.value).map(([code, items]) => ({
        code,
        name: code,
        items: items.map((item: DictionaryOption, index: number) => ({
          value: item.value,
          label: item.label,
          sort_order: item.sort_order ?? index,
          extra_json: item.extra_json,
        })),
      })),
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(payload))
  }

  function hydrateFromStorage() {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) {
      return
    }

    try {
      const parsed = JSON.parse(raw) as DictionaryCacheState
      fetchedAt.value = parsed.fetchedAt
      dictionaries.value = normalizeCache({ dictionaries: parsed.dictionaries })
    } catch {
      localStorage.removeItem(STORAGE_KEY)
    }
  }

  async function load(force = false) {
    if (loading.value) {
      return
    }
    if (!force && isLoaded.value && !isExpired.value) {
      return
    }

    loading.value = true
    try {
      const response = await systemDictionaryApi.getCache()
      dictionaries.value = normalizeCache(response.data)
      fetchedAt.value = Date.now()
      persistCache()
    } finally {
      loading.value = false
    }
  }

  async function ensureLoaded(force = false) {
    if (!isLoaded.value) {
      hydrateFromStorage()
    }
    await load(force)
  }

  function invalidate() {
    dictionaries.value = {}
    fetchedAt.value = 0
    localStorage.removeItem(STORAGE_KEY)
  }

  function getOptions(typeCode: string, fallback: DictionaryOption[] = []): DictionaryOption[] {
    const options = dictionaries.value[typeCode]
    return options && options.length > 0 ? options : fallback
  }

  function getOption(typeCode: string, value: string, fallback: DictionaryOption[] = []): DictionaryOption | null {
    return getOptions(typeCode, fallback).find((item: DictionaryOption) => item.value === value) ?? null
  }

  function getLabel(typeCode: string, value: string, fallback = value, optionsFallback: DictionaryOption[] = []): string {
    return getOption(typeCode, value, optionsFallback)?.label ?? fallback
  }

  function getSortOrder(
    typeCode: string,
    value: string,
    fallback = Number.MAX_SAFE_INTEGER,
    optionsFallback: DictionaryOption[] = [],
  ): number {
    return getOption(typeCode, value, optionsFallback)?.sort_order ?? fallback
  }

  function getExtra(
    typeCode: string,
    value: string,
    optionsFallback: DictionaryOption[] = [],
  ): Record<string, unknown> | null {
    return getOption(typeCode, value, optionsFallback)?.extra_json ?? null
  }

  return {
    dictionaries,
    fetchedAt,
    loading,
    isLoaded,
    isExpired,
    ensureLoaded,
    invalidate,
    getOptions,
    getOption,
    getLabel,
    getSortOrder,
    getExtra,
  }
})