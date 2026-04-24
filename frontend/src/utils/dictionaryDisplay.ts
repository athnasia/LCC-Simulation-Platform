import type { DictionaryTagType } from '@/constants/systemDictionaries'
import type { DictionaryOption } from '@/stores/dictionaries'

const VALID_TAG_TYPES = new Set<DictionaryTagType>(['primary', 'success', 'warning', 'info', 'danger'])

function getDictionaryOption(options: DictionaryOption[], value: string) {
  return options.find((option) => option.value === value)
}

export function resolveDictionaryLabel(options: DictionaryOption[], value: string, fallback = value): string {
  return getDictionaryOption(options, value)?.label ?? fallback
}

export function resolveDictionarySortOrder(
  options: DictionaryOption[],
  value: string,
  fallback = Number.MAX_SAFE_INTEGER,
): number {
  return getDictionaryOption(options, value)?.sort_order ?? fallback
}

export function resolveDictionaryTagType(
  options: DictionaryOption[],
  value: string,
  fallback?: DictionaryTagType,
): DictionaryTagType | undefined {
  const raw = getDictionaryOption(options, value)?.extra_json?.tag_type
  if (typeof raw === 'string' && VALID_TAG_TYPES.has(raw as DictionaryTagType)) {
    return raw as DictionaryTagType
  }
  return fallback
}

export function resolveDictionaryInputHint(
  options: DictionaryOption[],
  value: string,
  fallback: string,
): string {
  const raw = getDictionaryOption(options, value)?.extra_json?.input_hint
  if (typeof raw === 'string' && raw.trim()) {
    return raw
  }
  return fallback
}