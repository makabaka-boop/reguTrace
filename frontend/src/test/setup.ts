import { vi } from 'vitest'

const { mockRequest, mockMessage, mockRouter } = vi.hoisted(() => ({
  mockRequest: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
  mockMessage: {
    success: vi.fn(),
    error: vi.fn(),
    info: vi.fn(),
    warning: vi.fn(),
  },
  mockRouter: {
    push: vi.fn(),
    replace: vi.fn(),
  },
}))

vi.mock('@/api/request', () => ({
  default: mockRequest,
}))

vi.mock('ant-design-vue', () => ({
  message: mockMessage,
  Modal: {
    confirm: vi.fn(),
  },
}))

vi.mock('@/router', () => ({
  default: mockRouter,
}))

beforeEach(() => {
  mockRequest.get.mockReset()
  mockRequest.post.mockReset()
  mockRequest.put.mockReset()
  mockRequest.delete.mockReset()
  mockMessage.success.mockReset()
  mockMessage.error.mockReset()
  mockMessage.info.mockReset()
  mockMessage.warning.mockReset()
  mockRouter.push.mockReset()
  mockRouter.replace.mockReset()
  localStorage.clear()
})

export function okResponse<T>(data: T) {
  return Promise.resolve({ code: 200, message: 'success', data })
}

export function failResponse(message = 'Error') {
  return Promise.reject(new Error(message))
}

export { mockRequest, mockMessage, mockRouter }
