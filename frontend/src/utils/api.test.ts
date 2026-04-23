import { describe, it, expect, vi } from 'vitest'
import { createPageParams, createCrudApi, RequestCanceller } from './api'

describe('api utils', () => {
  describe('createPageParams', () => {
    it('should create page params with defaults', () => {
      const params = createPageParams({})
      expect(params).toEqual({
        keyword: '',
        page: 1,
        size: 20,
      })
    })

    it('should create page params with custom values', () => {
      const params = createPageParams({
        keyword: 'test',
        page: 2,
        size: 50,
      })
      expect(params).toEqual({
        keyword: 'test',
        page: 2,
        size: 50,
      })
    })
  })

  describe('createCrudApi', () => {
    it('should create CRUD API methods', () => {
      const api = createCrudApi<any, any, any>('/test')
      expect(api.list).toBeDefined()
      expect(api.detail).toBeDefined()
      expect(api.create).toBeDefined()
      expect(api.update).toBeDefined()
      expect(api.delete).toBeDefined()
      expect(api.batchDelete).toBeDefined()
    })
  })

  describe('RequestCanceller', () => {
    it('should create and cancel request', () => {
      const canceller = new RequestCanceller()
      const controller = canceller.create('test-key')
      
      expect(controller).toBeInstanceOf(AbortController)
      expect(controller.signal.aborted).toBe(false)
      
      canceller.cancel('test-key')
      expect(controller.signal.aborted).toBe(true)
    })

    it('should cancel all requests', () => {
      const canceller = new RequestCanceller()
      const controller1 = canceller.create('key1')
      const controller2 = canceller.create('key2')
      
      canceller.cancelAll()
      
      expect(controller1.signal.aborted).toBe(true)
      expect(controller2.signal.aborted).toBe(true)
    })

    it('should replace existing controller with same key', () => {
      const canceller = new RequestCanceller()
      const controller1 = canceller.create('same-key')
      const controller2 = canceller.create('same-key')
      
      expect(controller1.signal.aborted).toBe(true)
      expect(controller2.signal.aborted).toBe(false)
    })
  })
})
