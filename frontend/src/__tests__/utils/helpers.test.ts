import { describe, it, expect } from 'vitest'

const getStatusColor = (status: string): string => {
  const colors: Record<string, string> = {
    pending: 'orange',
    approved: 'green',
    rejected: 'red',
  }
  return colors[status] || 'default'
}

const getStatusLabel = (status: string): string => {
  const labels: Record<string, string> = {
    pending: '待复核',
    approved: '已通过',
    rejected: '已驳回',
  }
  return labels[status] || status
}

const getCycleLabel = (cycle?: string): string => {
  const labels: Record<string, string> = {
    '1month': '1个月',
    '3months': '3个月',
    '6months': '6个月',
    '1year': '1年',
    'never': '永不',
  }
  return labels[cycle || ''] || '未设置'
}

const getExpiryTagColor = (status?: string): string => {
  const colors: Record<string, string> = {
    normal: 'green',
    upcoming: 'orange',
    overdue: 'red',
  }
  return colors[status || ''] || ''
}

describe('page helper functions', () => {
  describe('getStatusColor', () => {
    it('returns correct color for known statuses', () => {
      expect(getStatusColor('pending')).toBe('orange')
      expect(getStatusColor('approved')).toBe('green')
      expect(getStatusColor('rejected')).toBe('red')
    })

    it('returns default for unknown status', () => {
      expect(getStatusColor('unknown')).toBe('default')
      expect(getStatusColor('')).toBe('default')
    })
  })

  describe('getStatusLabel', () => {
    it('returns Chinese labels for known statuses', () => {
      expect(getStatusLabel('pending')).toBe('待复核')
      expect(getStatusLabel('approved')).toBe('已通过')
      expect(getStatusLabel('rejected')).toBe('已驳回')
    })

    it('returns original string for unknown status', () => {
      expect(getStatusLabel('custom')).toBe('custom')
    })
  })

  describe('getCycleLabel', () => {
    it('returns Chinese labels for known cycles', () => {
      expect(getCycleLabel('1month')).toBe('1个月')
      expect(getCycleLabel('3months')).toBe('3个月')
      expect(getCycleLabel('6months')).toBe('6个月')
      expect(getCycleLabel('1year')).toBe('1年')
      expect(getCycleLabel('never')).toBe('永不')
    })

    it('returns 未设置 for undefined or unknown', () => {
      expect(getCycleLabel(undefined)).toBe('未设置')
      expect(getCycleLabel('')).toBe('未设置')
      expect(getCycleLabel('unknown')).toBe('未设置')
    })
  })

  describe('getExpiryTagColor', () => {
    it('returns correct colors', () => {
      expect(getExpiryTagColor('normal')).toBe('green')
      expect(getExpiryTagColor('upcoming')).toBe('orange')
      expect(getExpiryTagColor('overdue')).toBe('red')
    })

    it('returns empty string for undefined', () => {
      expect(getExpiryTagColor(undefined)).toBe('')
      expect(getExpiryTagColor('')).toBe('')
    })
  })
})
