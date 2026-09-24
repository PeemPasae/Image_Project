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

describe('getHistory contract — regression for Home.jsx crash', () => {
  it.skip('FAILS when backend returns a bare array instead of { history, pagination }', async () => {
    // This mirrors what we suspect the real Backend is doing right now —
    // sending data as a plain array instead of { history: [...], pagination: {...} }.
    mockClient.get.mockResolvedValueOnce(
      envelope([{ id: 1, prompt: 'x', checkpoint: 'anypastel', width: 512, height: 512 }])
    )
    const data = await api.getHistory()
    // If this assertion fails, it confirms Home.jsx's `data.history` is undefined
    // for the same reason getModels() broke — Backend contract mismatch.
    expect(data.history).toBeDefined()
  })
})
describe('processSpotBlur contract', () => {
  beforeEach(() => {
    // jsdom has no URL.createObjectURL
    URL.createObjectURL = vi.fn(() => 'blob:mock-result')
  })

  it('posts multipart form with image/circles/strength/soft and returns a blob URL', async () => {
    const png = new Blob(['png-bytes'], { type: 'image/png' })
    mockClient.post.mockResolvedValueOnce({ data: png })
    const file = new File(['img'], 'photo.jpg', { type: 'image/jpeg' })

    const url = await api.processSpotBlur(file, [[120, 340, 38], [210, 300, 38]], 12)

    expect(url).toBe('blob:mock-result')
    expect(URL.createObjectURL).toHaveBeenCalledWith(png)

    const [path, form, config] = mockClient.post.mock.calls[0]
    expect(path).toBe('/process/spot-blur')
    expect(form).toBeInstanceOf(FormData)
    expect(form.get('image')).toBeInstanceOf(File)
    expect(form.get('circles')).toBe('[[120,340,38],[210,300,38]]')
    expect(form.get('strength')).toBe('12')
    expect(form.get('soft')).toBe('true')
    expect(config).toMatchObject({
      responseType: 'blob',
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  })

  it('throws with .code parsed from a Blob error body', async () => {
    const body = new Blob(
      [JSON.stringify({ success: false, error: { code: 'VALIDATION_ERROR', message: 'circles must not be empty' } })],
      { type: 'application/json' }
    )
    mockClient.post.mockRejectedValueOnce({ response: { data: body } })
    const file = new File(['img'], 'photo.png', { type: 'image/png' })

    await expect(api.processSpotBlur(file, [], 10)).rejects.toMatchObject({
      code: 'VALIDATION_ERROR',
      message: 'circles must not be empty',
    })
  })
})

describe('processCartoonize contract', () => {
  beforeEach(() => {
    URL.createObjectURL = vi.fn(() => 'blob:mock-result')
  })

  it('posts multipart form with image/num_colors/line_thickness/smoothness and returns a blob URL', async () => {
    const png = new Blob(['png-bytes'], { type: 'image/png' })
    mockClient.post.mockResolvedValueOnce({ data: png })
    const file = new File(['img'], 'photo.jpg', { type: 'image/jpeg' })

    const url = await api.processCartoonize(file, { num_colors: 16, line_thickness: 3, smoothness: 7 })

    expect(url).toBe('blob:mock-result')
    expect(URL.createObjectURL).toHaveBeenCalledWith(png)

    const [path, form, config] = mockClient.post.mock.calls[0]
    expect(path).toBe('/process/cartoonize')
    expect(form).toBeInstanceOf(FormData)
    expect(form.get('image')).toBeInstanceOf(File)
    expect(form.get('num_colors')).toBe('16')
    expect(form.get('line_thickness')).toBe('3')
    expect(form.get('smoothness')).toBe('7')
    expect(config).toMatchObject({
      responseType: 'blob',
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  })

  it('throws with .code parsed from a Blob error body', async () => {
    const body = new Blob(
      [JSON.stringify({ success: false, error: { code: 'VALIDATION_ERROR', message: 'num_colors must be 4-32' } })],
      { type: 'application/json' }
    )
    mockClient.post.mockRejectedValueOnce({ response: { data: body } })
    const file = new File(['img'], 'photo.png', { type: 'image/png' })

    await expect(api.processCartoonize(file, { num_colors: 100 })).rejects.toMatchObject({
      code: 'VALIDATION_ERROR',
      message: 'num_colors must be 4-32',
    })
  })
})

describe('processTiltShift contract', () => {
  beforeEach(() => {
    URL.createObjectURL = vi.fn(() => 'blob:mock-result')
  })

  it('posts multipart form with all tilt-shift fields and returns a blob URL', async () => {
    const png = new Blob(['png-bytes'], { type: 'image/png' })
    mockClient.post.mockResolvedValueOnce({ data: png })
    const file = new File(['img'], 'photo.jpg', { type: 'image/jpeg' })

    const url = await api.processTiltShift(file, {
      focus_position: 0.4,
      focus_width: 0.3,
      blur_strength: 20,
      saturation_boost: 1.8,
      contrast_boost: 1.5,
    })

    expect(url).toBe('blob:mock-result')
    expect(URL.createObjectURL).toHaveBeenCalledWith(png)

    const [path, form, config] = mockClient.post.mock.calls[0]
    expect(path).toBe('/process/tilt-shift')
    expect(form).toBeInstanceOf(FormData)
    expect(form.get('image')).toBeInstanceOf(File)
    expect(form.get('focus_position')).toBe('0.4')
    expect(form.get('focus_width')).toBe('0.3')
    expect(form.get('blur_strength')).toBe('20')
    expect(form.get('saturation_boost')).toBe('1.8')
    expect(form.get('contrast_boost')).toBe('1.5')
    expect(config).toMatchObject({
      responseType: 'blob',
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  })

  it('throws with .code parsed from a Blob error body', async () => {
    const body = new Blob(
      [JSON.stringify({ success: false, error: { code: 'VALIDATION_ERROR', message: 'blur_strength must be 1-30' } })],
      { type: 'application/json' }
    )
    mockClient.post.mockRejectedValueOnce({ response: { data: body } })
    const file = new File(['img'], 'photo.png', { type: 'image/png' })

    await expect(api.processTiltShift(file, { blur_strength: 99 })).rejects.toMatchObject({
      code: 'VALIDATION_ERROR',
      message: 'blur_strength must be 1-30',
    })
  })
})

describe('processHdrEnhancer contract', () => {
  beforeEach(() => {
    URL.createObjectURL = vi.fn(() => 'blob:mock-result')
  })

  it('posts multipart form with all hdr-enhancer fields (color_balance sent as a string) and returns a blob URL', async () => {
    const png = new Blob(['png-bytes'], { type: 'image/png' })
    mockClient.post.mockResolvedValueOnce({ data: png })
    const file = new File(['img'], 'photo.jpg', { type: 'image/jpeg' })

    const url = await api.processHdrEnhancer(file, {
      clahe_clip_limit: 2.5,
      clahe_grid_size: 12,
      detail_strength: 2.0,
      color_balance: false,
    })

    expect(url).toBe('blob:mock-result')
    expect(URL.createObjectURL).toHaveBeenCalledWith(png)

    const [path, form, config] = mockClient.post.mock.calls[0]
    expect(path).toBe('/process/hdr-enhancer')
    expect(form).toBeInstanceOf(FormData)
    expect(form.get('image')).toBeInstanceOf(File)
    expect(form.get('clahe_clip_limit')).toBe('2.5')
    expect(form.get('clahe_grid_size')).toBe('12')
    expect(form.get('detail_strength')).toBe('2')
    expect(form.get('color_balance')).toBe('false')
    expect(config).toMatchObject({
      responseType: 'blob',
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  })

  it('throws with .code parsed from a Blob error body', async () => {
    const body = new Blob(
      [JSON.stringify({ success: false, error: { code: 'VALIDATION_ERROR', message: 'clahe_grid_size must be 2-16' } })],
      { type: 'application/json' }
    )
    mockClient.post.mockRejectedValueOnce({ response: { data: body } })
    const file = new File(['img'], 'photo.png', { type: 'image/png' })

    await expect(api.processHdrEnhancer(file, { clahe_grid_size: 100 })).rejects.toMatchObject({
      code: 'VALIDATION_ERROR',
      message: 'clahe_grid_size must be 2-16',
    })
  })
})
