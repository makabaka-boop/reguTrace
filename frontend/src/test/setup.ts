/**
 * Vitest 全局初始化。
 *
 * - 提供最小化的 localStorage、window.location 存根，供 store/api 层使用；
 * - 全局 mock ant-design-vue 的 message/Modal，避免测试触发真实 UI。
 */
import { vi, beforeEach } from 'vitest'
import { config } from '@vue/test-utils'

// 关闭对未注册的 a-* 组件解析告警：单元测试关注方法逻辑而非真实渲染。
config.global.config = config.global.config || {}
config.global.config.warnHandler = () => {}

// ant-design-vue 的 message 与 Modal 在被测代码中被广泛调用，
// 统一 mock 为可断言的 spy，防止实例化真实组件。
vi.mock('ant-design-vue', () => {
  const message = {
    success: vi.fn(),
    error: vi.fn(),
    info: vi.fn(),
    warning: vi.fn(),
    loading: vi.fn(),
  }
  const Modal = {
    confirm: vi.fn(),
    info: vi.fn(),
    warning: vi.fn(),
  }
  return { message, Modal }
})

// 全局路由 mock，供 store 中的 router.push 使用。
vi.mock('@/router', () => ({
  default: { push: vi.fn() },
}))

// happy-dom 已提供 localStorage，但确保每个用例前清空，避免串扰。
beforeEach(() => {
  localStorage.clear()
  vi.clearAllMocks()
})
