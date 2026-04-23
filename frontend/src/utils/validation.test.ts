import { describe, it, expect } from 'vitest'
import {
  requiredRule,
  emailRule,
  phoneRule,
  codeRule,
  minLengthRule,
  maxLengthRule,
  lengthRangeRule,
  patternRule,
  passwordRule,
  integerRule,
  positiveIntegerRule,
  numberRule,
  nonNegativeNumberRule,
  commonRules,
} from './validation'

describe('validation rules', () => {
  describe('requiredRule', () => {
    it('should create a required rule with message', () => {
      const rule = requiredRule('请输入用户名')
      expect(rule.required).toBe(true)
      expect(rule.message).toBe('请输入用户名')
      expect(rule.trigger).toBe('blur')
    })

    it('should create a required rule with custom trigger', () => {
      const rule = requiredRule('请选择选项', 'change')
      expect(rule.trigger).toBe('change')
    })
  })

  describe('emailRule', () => {
    it('should create an email rule with default message', () => {
      const rule = emailRule()
      expect(rule.type).toBe('email')
      expect(rule.message).toBe('请输入正确的邮箱地址')
    })

    it('should create an email rule with custom message', () => {
      const rule = emailRule('邮箱格式不正确')
      expect(rule.message).toBe('邮箱格式不正确')
    })
  })

  describe('phoneRule', () => {
    it('should create a phone rule with pattern', () => {
      const rule = phoneRule()
      expect(rule.pattern).toBeInstanceOf(RegExp)
      expect(rule.message).toBe('请输入正确的手机号')
    })

    it('should validate correct phone numbers', () => {
      const rule = phoneRule()
      const pattern = rule.pattern as RegExp
      expect(pattern.test('13800138000')).toBe(true)
      expect(pattern.test('15912345678')).toBe(true)
      expect(pattern.test('12345678901')).toBe(false)
      expect(pattern.test('1380013800')).toBe(false)
    })
  })

  describe('codeRule', () => {
    it('should create a code rule with pattern', () => {
      const rule = codeRule()
      expect(rule.pattern).toBeInstanceOf(RegExp)
      expect(rule.message).toBe('编码只能包含大写字母、数字和下划线')
    })

    it('should validate correct codes', () => {
      const rule = codeRule()
      const pattern = rule.pattern as RegExp
      expect(pattern.test('ABC_123')).toBe(true)
      expect(pattern.test('PROJECT_001')).toBe(true)
      expect(pattern.test('abc')).toBe(false)
      expect(pattern.test('ABC-123')).toBe(false)
    })
  })

  describe('minLengthRule', () => {
    it('should create a min length rule', () => {
      const rule = minLengthRule(6)
      expect(rule.min).toBe(6)
      expect(rule.message).toBe('长度不能少于 6 个字符')
    })

    it('should create a min length rule with custom message', () => {
      const rule = minLengthRule(8, '密码至少8位')
      expect(rule.message).toBe('密码至少8位')
    })
  })

  describe('maxLengthRule', () => {
    it('should create a max length rule', () => {
      const rule = maxLengthRule(100)
      expect(rule.max).toBe(100)
      expect(rule.message).toBe('长度不能超过 100 个字符')
    })
  })

  describe('lengthRangeRule', () => {
    it('should create a length range rule', () => {
      const rule = lengthRangeRule(3, 20)
      expect(rule.min).toBe(3)
      expect(rule.max).toBe(20)
      expect(rule.message).toBe('长度必须在 3 到 20 个字符之间')
    })
  })

  describe('patternRule', () => {
    it('should create a pattern rule', () => {
      const pattern = /^[A-Z]+$/
      const rule = patternRule(pattern, '只能输入大写字母')
      expect(rule.pattern).toBe(pattern)
      expect(rule.message).toBe('只能输入大写字母')
    })
  })

  describe('passwordRule', () => {
    it('should create a password rule', () => {
      const rule = passwordRule()
      expect(rule.pattern).toBeInstanceOf(RegExp)
      expect(rule.message).toBe('密码必须包含字母和数字，长度至少6位')
    })

    it('should validate correct passwords', () => {
      const rule = passwordRule()
      const pattern = rule.pattern as RegExp
      expect(pattern.test('abc123')).toBe(true)
      expect(pattern.test('ABC123')).toBe(true)
      expect(pattern.test('Password123')).toBe(true)
      expect(pattern.test('123456')).toBe(false)
      expect(pattern.test('abcdef')).toBe(false)
      expect(pattern.test('abc12')).toBe(false)
    })
  })

  describe('integerRule', () => {
    it('should validate integers', () => {
      const rule = integerRule()
      const pattern = rule.pattern as RegExp
      expect(pattern.test('123')).toBe(true)
      expect(pattern.test('-123')).toBe(true)
      expect(pattern.test('0')).toBe(true)
      expect(pattern.test('12.3')).toBe(false)
      expect(pattern.test('abc')).toBe(false)
    })
  })

  describe('positiveIntegerRule', () => {
    it('should validate positive integers', () => {
      const rule = positiveIntegerRule()
      const pattern = rule.pattern as RegExp
      expect(pattern.test('123')).toBe(true)
      expect(pattern.test('1')).toBe(true)
      expect(pattern.test('0')).toBe(false)
      expect(pattern.test('-1')).toBe(false)
      expect(pattern.test('12.3')).toBe(false)
    })
  })

  describe('numberRule', () => {
    it('should validate numbers', () => {
      const rule = numberRule()
      const pattern = rule.pattern as RegExp
      expect(pattern.test('123')).toBe(true)
      expect(pattern.test('-123')).toBe(true)
      expect(pattern.test('12.34')).toBe(true)
      expect(pattern.test('-12.34')).toBe(true)
      expect(pattern.test('abc')).toBe(false)
    })
  })

  describe('nonNegativeNumberRule', () => {
    it('should validate non-negative numbers', () => {
      const rule = nonNegativeNumberRule()
      const pattern = rule.pattern as RegExp
      expect(pattern.test('123')).toBe(true)
      expect(pattern.test('0')).toBe(true)
      expect(pattern.test('12.34')).toBe(true)
      expect(pattern.test('-1')).toBe(false)
      expect(pattern.test('-12.34')).toBe(false)
    })
  })

  describe('commonRules', () => {
    it('should have username rules', () => {
      expect(commonRules.username).toHaveLength(2)
      expect(commonRules.username[0].required).toBe(true)
    })

    it('should have password rules', () => {
      expect(commonRules.password).toHaveLength(2)
      expect(commonRules.password[0].required).toBe(true)
    })

    it('should have email rules', () => {
      expect(commonRules.email).toHaveLength(2)
      expect(commonRules.email[0].required).toBe(true)
    })

    it('should have code rules', () => {
      expect(commonRules.code).toHaveLength(2)
      expect(commonRules.code[0].required).toBe(true)
    })

    it('should have name rules', () => {
      expect(commonRules.name).toHaveLength(2)
      expect(commonRules.name[0].required).toBe(true)
    })
  })
})
