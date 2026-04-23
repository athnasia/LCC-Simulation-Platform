/**
 * 表单验证规则工具函数
 * 
 * 提供常用的表单验证规则，确保验证逻辑的一致性
 */

import type { FormRule } from '@/types/common'

/**
 * 必填验证规则
 */
export function requiredRule(message: string, trigger: 'blur' | 'change' = 'blur'): FormRule {
  return { required: true, message, trigger }
}

/**
 * 邮箱验证规则
 */
export function emailRule(message = '请输入正确的邮箱地址', trigger: 'blur' | 'change' = 'blur'): FormRule {
  return {
    type: 'email',
    message,
    trigger,
  }
}

/**
 * 手机号验证规则
 */
export function phoneRule(message = '请输入正确的手机号', trigger: 'blur' | 'change' = 'blur'): FormRule {
  return {
    pattern: /^1[3-9]\d{9}$/,
    message,
    trigger,
  }
}

/**
 * 编码验证规则（大写字母、数字、下划线）
 */
export function codeRule(message = '编码只能包含大写字母、数字和下划线', trigger: 'blur' | 'change' = 'blur'): FormRule {
  return {
    pattern: /^[A-Z0-9_]+$/,
    message,
    trigger,
  }
}

/**
 * 最小长度验证规则
 */
export function minLengthRule(min: number, message?: string, trigger: 'blur' | 'change' = 'blur'): FormRule {
  return {
    min,
    message: message || `长度不能少于 ${min} 个字符`,
    trigger,
  }
}

/**
 * 最大长度验证规则
 */
export function maxLengthRule(max: number, message?: string, trigger: 'blur' | 'change' = 'blur'): FormRule {
  return {
    max,
    message: message || `长度不能超过 ${max} 个字符`,
    trigger,
  }
}

/**
 * 长度范围验证规则
 */
export function lengthRangeRule(min: number, max: number, message?: string, trigger: 'blur' | 'change' = 'blur'): FormRule {
  return {
    min,
    max,
    message: message || `长度必须在 ${min} 到 ${max} 个字符之间`,
    trigger,
  }
}

/**
 * 数字范围验证规则
 */
export function numberRangeRule(min: number, max: number, message?: string, trigger: 'blur' | 'change' = 'blur'): FormRule {
  return {
    type: 'number',
    min,
    max,
    message: message || `数值必须在 ${min} 到 ${max} 之间`,
    trigger,
  }
}

/**
 * 正则验证规则
 */
export function patternRule(pattern: RegExp, message: string, trigger: 'blur' | 'change' = 'blur'): FormRule {
  return {
    pattern,
    message,
    trigger,
  }
}

/**
 * 密码强度验证规则
 */
export function passwordRule(message = '密码必须包含字母和数字，长度至少6位', trigger: 'blur' | 'change' = 'blur'): FormRule {
  return {
    pattern: /^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d@$!%*#?&]{6,}$/,
    message,
    trigger,
  }
}

/**
 * URL 验证规则
 */
export function urlRule(message = '请输入正确的URL地址', trigger: 'blur' | 'change' = 'blur'): FormRule {
  return {
    type: 'url',
    message,
    trigger,
  }
}

/**
 * 整数验证规则
 */
export function integerRule(message = '请输入整数', trigger: 'blur' | 'change' = 'blur'): FormRule {
  return {
    pattern: /^-?\d+$/,
    message,
    trigger,
  }
}

/**
 * 正整数验证规则
 */
export function positiveIntegerRule(message = '请输入正整数', trigger: 'blur' | 'change' = 'blur'): FormRule {
  return {
    pattern: /^[1-9]\d*$/,
    message,
    trigger,
  }
}

/**
 * 数字验证规则
 */
export function numberRule(message = '请输入数字', trigger: 'blur' | 'change' = 'blur'): FormRule {
  return {
    pattern: /^-?\d+(\.\d+)?$/,
    message,
    trigger,
  }
}

/**
 * 非负数验证规则
 */
export function nonNegativeNumberRule(message = '请输入非负数', trigger: 'blur' | 'change' = 'blur'): FormRule {
  return {
    pattern: /^\d+(\.\d+)?$/,
    message,
    trigger,
  }
}

/**
 * 常用规则组合
 */
export const commonRules = {
  username: [
    requiredRule('请输入用户名'),
    lengthRangeRule(3, 20, '用户名长度必须在3到20个字符之间'),
  ],
  password: [
    requiredRule('请输入密码'),
    passwordRule(),
  ],
  email: [
    requiredRule('请输入邮箱'),
    emailRule(),
  ],
  phone: [
    phoneRule(),
  ],
  code: [
    requiredRule('请输入编码'),
    codeRule(),
  ],
  name: [
    requiredRule('请输入名称'),
    maxLengthRule(100),
  ],
  description: [
    maxLengthRule(500),
  ],
}
