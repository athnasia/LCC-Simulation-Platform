/**
 * 格式化工具函数
 *
 * 提供常用的数据格式化函数，确保显示格式的一致性
 */

/**
 * 格式化 ISO 日期字符串为本地化显示
 * @param value ISO 日期字符串
 * @returns 本地化日期时间字符串
 */
export function formatDate(value: string): string {
  return new Date(value).toLocaleString('zh-CN', { hour12: false })
}

/**
 * 格式化换算系数
 * @param value 换算系数值
 * @param fallback 未配置时的显示文本
 * @returns 格式化后的系数字符串
 */
export function formatFactor(value: number | undefined, fallback = '未配置'): string {
  if (value === undefined) {
    return fallback
  }
  return Number(value).toFixed(6).replace(/\.?0+$/, '')
}

/**
 * 格式化价格显示
 * @param value 价格值
 * @param prefix 货币符号前缀
 * @param decimals 小数位数
 * @returns 格式化后的价格字符串
 */
export function formatPrice(
  value: number | string | null | undefined,
  prefix = '¥',
  decimals = 4
): string {
  if (value === null || value === undefined) {
    return '-'
  }
  return `${prefix}${Number(value).toFixed(decimals)}`
}

/**
 * 格式化百分比显示
 * @param value 百分比值（如 0.15 表示 15%）
 * @param decimals 小数位数
 * @returns 格式化后的百分比字符串
 */
export function formatPercent(value: number | null | undefined, decimals = 2): string {
  if (value === null || value === undefined) {
    return '-'
  }
  return `${(value * 100).toFixed(decimals)}%`
}

/**
 * 格式化数字显示（添加千分位）
 * @param value 数值
 * @param decimals 小数位数
 * @returns 格式化后的数字字符串
 */
export function formatNumber(value: number | null | undefined, decimals = 2): string {
  if (value === null || value === undefined) {
    return '-'
  }
  return Number(value).toLocaleString('zh-CN', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })
}

/**
 * 格式化文件大小
 * @param bytes 字节数
 * @returns 格式化后的文件大小字符串
 */
export function formatFileSize(bytes: number | null | undefined): string {
  if (bytes === null || bytes === undefined) {
    return '-'
  }
  if (bytes === 0) {
    return '0 B'
  }
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  const k = 1024
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${(bytes / Math.pow(k, i)).toFixed(2)} ${units[i]}`
}
