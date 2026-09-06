import axios from 'axios'
import {
  MOCK_USER, MOCK_MODELS, MOCK_GENERATIONS, MOCK_PROFILE,
  mockImageUrlFor, delay,
} from './mockData'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api/v1'
const DEFAULT_TIMEOUT = 20000
// /generate can take 10-60s+ on the AI server — give it real headroom (locked: 90s)
export const GENERATE_TIMEOUT = 90000

// Dev Preview Mode: browse every page with realistic fake data, no Backend needed.
// Toggle via VITE_MOCK_MODE=true in .env. Every mock branch mirrors the exact
// {success,data} shape the real API returns, so flipping this off requires no
// page-level code changes.
export const MOCK_MODE = import.meta.env.VITE_MOCK_MODE === 'true'

const client = axios.create({
  baseURL: BASE_URL,
  timeout: DEFAULT_TIMEOUT,
})

// Attach JWT to every request if present
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('luma_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Unwrap { success, data } / throw on { success:false, error } — single place every
// page relies on so nobody has to re-implement envelope parsing per call.
client.interceptors.response.use(
  (response) => response,
  (error) => {
    const code = error.response?.data?.error?.code
    if (code === 'UNAUTHORIZED') {
      localStorage.removeItem('luma_token')
      localStorage.removeItem('luma_user')
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

/**
 * Wraps an axios call, unwraps the envelope, and normalizes errors into
 * a plain Error with .code and .message set from the API contract.
 */
async function request(promise) {
  try {
    const res = await promise
    return res.data?.data
  } catch (err) {
    const apiError = err.response?.data?.error
    const message = apiError?.message || err.message || 'Something went wrong'
    const wrapped = new Error(message)
    wrapped.code = apiError?.code || (err.code === 'ECONNABORTED' ? 'AI_SERVER_TIMEOUT' : 'NETWORK_ERROR')
    throw wrapped
  }
}

export const api = {
  register: (email, password) => {
    if (MOCK_MODE) return delay().then(() => ({ message: 'Registration successful' }))
    return request(client.post('/register', { email, password }))
  },

  login: (email, password) => {
    if (MOCK_MODE) return delay().then(() => ({ access_token: 'mock-token', user: MOCK_USER }))
    return request(client.post('/login', { email, password }))
  },

  getModels: () => {
    if (MOCK_MODE) return delay().then(() => ({ models: MOCK_MODELS }))
    return request(client.get('/models'))
  },

  generate: (payload) => {
    if (MOCK_MODE) {
      return delay(1200).then(() => ({
        generation_id: 1,
        image_url: '/mock/images/1',
        seed: payload.seed === -1 ? Math.floor(Math.random() * 1e9) : payload.seed,
        created_at: new Date().toISOString(),
      }))
    }
    return request(client.post('/generate', payload, { timeout: GENERATE_TIMEOUT }))
  },

  getHistory: (page = 1, limit = 20) => {
    if (MOCK_MODE) {
      return delay().then(() => ({
        history: MOCK_GENERATIONS,
        pagination: { page: 1, limit, total: MOCK_GENERATIONS.length, total_pages: 1 },
      }))
    }
    return request(client.get('/history', { params: { page, limit } }))
  },

  getGeneration: (id) => {
    if (MOCK_MODE) {
      const gen = MOCK_GENERATIONS.find((g) => String(g.id) === String(id)) || MOCK_GENERATIONS[0]
      return delay().then(() => ({ ...gen, image_url: `/mock/images/${gen.id}` }))
    }
    return request(client.get(`/history/${id}`))
  },

  deleteGeneration: (id) => {
    if (MOCK_MODE) return delay().then(() => ({ message: 'Generation deleted successfully' }))
    return request(client.delete(`/history/${id}`))
  },

  getProfile: () => {
    if (MOCK_MODE) return delay().then(() => MOCK_PROFILE)
    return request(client.get('/profile'))
  },

  /** Fetches an authenticated image as a Blob (plain <img src> can't send headers). */
  getImageBlob: (imageUrl) => {
    if (MOCK_MODE) {
      const id = imageUrl.split('/').pop()
      return Promise.resolve(mockImageUrlFor(id))
    }
    return client.get(imageUrl, { baseURL: BASE_URL.replace(/\/api\/v1$/, ''), responseType: 'blob' })
      .then((res) => URL.createObjectURL(res.data))
  },
}

export default client
