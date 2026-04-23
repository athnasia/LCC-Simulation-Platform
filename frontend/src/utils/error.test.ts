import { describe, it, expect, vi, beforeEach } from 'vitest'
import {
  ErrorType,
  parseErrorType,
  getErrorMessage,
  showError,
  showSuccess,
  showWarning,
  showInfo,
  logError,
} from './error'
import { ElMessage, ElNotification } from 'element-plus'

describe('error utils', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('parseErrorType', () => {
    it('should return NETWORK for no response', () => {
      const error = { message: 'Network Error' }
      expect(parseErrorType(error)).toBe(ErrorType.NETWORK)
    })

    it('should return NETWORK for timeout', () => {
      const error = { code: 'ECONNABORTED' }
      expect(parseErrorType(error)).toBe(ErrorType.NETWORK)
    })

    it('should return AUTH for 401', () => {
      const error = { response: { status: 401 } }
      expect(parseErrorType(error)).toBe(ErrorType.AUTH)
    })

    it('should return PERMISSION for 403', () => {
      const error = { response: { status: 403 } }
      expect(parseErrorType(error)).toBe(ErrorType.PERMISSION)
    })

    it('should return NOT_FOUND for 404', () => {
      const error = { response: { status: 404 } }
      expect(parseErrorType(error)).toBe(ErrorType.NOT_FOUND)
    })

    it('should return VALIDATION for 422', () => {
      const error = { response: { status: 422 } }
      expect(parseErrorType(error)).toBe(ErrorType.VALIDATION)
    })

    it('should return SERVER for 500', () => {
      const error = { response: { status: 500 } }
      expect(parseErrorType(error)).toBe(ErrorType.SERVER)
    })

    it('should return SERVER for 502', () => {
      const error = { response: { status: 502 } }
      expect(parseErrorType(error)).toBe(ErrorType.SERVER)
    })

    it('should return UNKNOWN for other status', () => {
      const error = { response: { status: 418 } }
      expect(parseErrorType(error)).toBe(ErrorType.UNKNOWN)
    })
  })

  describe('getErrorMessage', () => {
    it('should return string error directly', () => {
      expect(getErrorMessage('Error message')).toBe('Error message')
    })

    it('should return response data message', () => {
      const error = {
        response: {
          data: { message: 'Custom error message' },
        },
      }
      expect(getErrorMessage(error)).toBe('Custom error message')
    })

    it('should return detail string', () => {
      const error = {
        response: {
          data: { detail: 'Detail error message' },
        },
      }
      expect(getErrorMessage(error)).toBe('Detail error message')
    })

    it('should join detail array messages', () => {
      const error = {
        response: {
          data: {
            detail: [
              { msg: 'Field A is required' },
              { msg: 'Field B is invalid' },
            ],
          },
        },
      }
      expect(getErrorMessage(error)).toBe('Field A is required；Field B is invalid')
    })

    it('should return default message for unknown error', () => {
      const error = {}
      expect(getErrorMessage(error)).toBe('操作失败')
    })
  })

  describe('showError', () => {
    it('should show notification for auth error', () => {
      const error = { response: { status: 401 } }
      showError(error)
      expect(ElNotification).toHaveBeenCalled()
    })

    it('should show warning for permission error', () => {
      const error = { response: { status: 403, data: { message: 'No permission' } } }
      showError(error)
      expect(ElMessage.warning).toHaveBeenCalled()
    })

    it('should show error message for other errors', () => {
      const error = { response: { status: 500, data: { message: 'Server error' } } }
      showError(error)
      expect(ElMessage.error).toHaveBeenCalled()
    })
  })

  describe('showSuccess', () => {
    it('should show success message', () => {
      showSuccess('Operation successful')
      expect(ElMessage.success).toHaveBeenCalledWith('Operation successful')
    })
  })

  describe('showWarning', () => {
    it('should show warning message', () => {
      showWarning('Warning message')
      expect(ElMessage.warning).toHaveBeenCalledWith('Warning message')
    })
  })

  describe('showInfo', () => {
    it('should show info message', () => {
      showInfo('Info message')
      expect(ElMessage.info).toHaveBeenCalledWith('Info message')
    })
  })

  describe('logError', () => {
    it('should log error to console', () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      const error = { message: 'Test error', response: { status: 500 } }
      logError(error, 'TestContext')
      expect(consoleSpy).toHaveBeenCalled()
      consoleSpy.mockRestore()
    })
  })
})
