import { describe, it, expect, vi, beforeEach } from 'vitest'

// vi.mock() is hoisted above imports by Vitest, so any variable it
// references must be created via vi.hoisted() — a plain `const` here
// would throw "Cannot access before initialization".
const { mockClient } = vi.hoisted(() => {
  const mockClient = {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
  }
  return { mockClient }
})

vi.mock('axios', () => ({
  default: { create: vi.fn(() => mockClient) },
}))

import { api } from '../api/client'

function envelope(data) {
  return { data: { success: true, data } }
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('login contract', () => {
  it('returns access_token and user', async () => {
    mockClient.post.mockResolvedValueOnce(
      envelope({ access_token: 'abc.jwt', user: { id: 1, email: 'a@a.com' } })
    )
    const data = await api.login('a@a.com', 'password123')
    expect(data).toHaveProperty('access_token')
    expect(data.user).toHaveProperty('email')
  })

  it('throws with .code on invalid credentials', async () => {
    mockClient.post.mockRejectedValueOnce({
      response: { data: { error: { code: 'INVALID_CREDENTIALS', message: 'Invalid email or password' } } },
    })
    await expect(api.login('a@a.com', 'wrong')).rejects.toMatchObject({
      code: 'INVALID_CREDENTIALS',
    })
  })
})

describe('getModels contract', () => {
  it('returns { models: [{ title, model_name }] }', async () => {
    mockClient.get.mockResolvedValueOnce(
      envelope({ models: [{ title: 'anypastel', model_name: 'anypastel' }] })
    )
    const data = await api.getModels()
    expect(Array.isArray(data.models)).toBe(true)
    expect(data.models[0]).toHaveProperty('model_name')
    expect(data.models[0]).toHaveProperty('title')
  })
})

describe('generate contract', () => {
  it('returns generation_id used for navigation', async () => {
    mockClient.post.mockResolvedValueOnce(
      envelope({ generation_id: 42, image_url: '/images/42', seed: 123, created_at: '2026-09-07T00:00:00Z' })
    )
    const data = await api.generate({ prompt: 'test', width: 512, height: 512 })
    expect(data).toHaveProperty('generation_id')
    expect(typeof data.generation_id).not.toBe('undefined')
  })
})

describe('getHistory contract', () => {
  it('returns { history: [...], pagination: {...} } with required fields', async () => {
    mockClient.get.mockResolvedValueOnce(
      envelope({
        history: [{ id: 1, prompt: 'x', checkpoint: 'anypastel', width: 512, height: 512 }],
        pagination: { page: 1, limit: 20, total: 1, total_pages: 1 },
      })
    )
    const data = await api.getHistory()
    expect(Array.isArray(data.history)).toBe(true)
    expect(data.history[0]).toEqual(
      expect.objectContaining({ id: expect.anything(), prompt: expect.any(String) })
    )
    expect(data.pagination).toEqual(
      expect.objectContaining({ page: expect.any(Number), total_pages: expect.any(Number) })
    )
  })
})

describe('getGeneration contract', () => {
  it('returns image_url, seed, created_at', async () => {
    mockClient.get.mockResolvedValueOnce(
      envelope({ id: 1, image_url: '/images/1', seed: 1, created_at: '2026-09-07T00:00:00Z' })
    )
    const data = await api.getGeneration(1)
    expect(data).toHaveProperty('image_url')
    expect(data).toHaveProperty('seed')
    expect(data).toHaveProperty('created_at')
  })
})

describe('getProfile contract', () => {
  it('returns generation_count, email, created_at', async () => {
    mockClient.get.mockResolvedValueOnce(
      envelope({ id: 1, email: 'a@a.com', created_at: '2026-09-07T00:00:00Z', generation_count: 3 })
    )
    const profile = await api.getProfile()
    expect(profile).toHaveProperty('generation_count')
    expect(profile).toHaveProperty('email')
    expect(profile).toHaveProperty('created_at')
  })
})

describe('error normalization', () => {
  it('maps a timed-out request to AI_SERVER_TIMEOUT', async () => {
    mockClient.post.mockRejectedValueOnce({ code: 'ECONNABORTED', message: 'timeout of 90000ms exceeded' })
    await expect(api.generate({ prompt: 'x' })).rejects.toMatchObject({
      code: 'AI_SERVER_TIMEOUT',
    })
  })
})