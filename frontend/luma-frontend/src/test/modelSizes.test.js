import { describe, it, expect } from 'vitest'
import { isRecommendedSize } from '../utils/modelSizes'

describe('isRecommendedSize', () => {
  it('accepts the recommended sizes', () => {
    expect(isRecommendedSize(512, 1024)).toBe(true)
    expect(isRecommendedSize(1024, 512)).toBe(true)
    expect(isRecommendedSize('512', '1024')).toBe(true)
  })
  it('rejects everything else', () => {
    expect(isRecommendedSize(512, 512)).toBe(false)
    expect(isRecommendedSize(768, 768)).toBe(false)
    expect(isRecommendedSize(1024, 1024)).toBe(false)
    expect(isRecommendedSize(undefined, undefined)).toBe(false)
  })
})
