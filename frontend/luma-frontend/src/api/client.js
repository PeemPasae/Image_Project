import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api/v1'
const DEFAULT_TIMEOUT = 20000
// /generate can take 10-60s+ on the AI server — give it real headroom (locked: 90s)
export const GENERATE_TIMEOUT = 90000

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
  register: (email, password) =>
    request(client.post('/register', { email, password })),

  login: (email, password) =>
    request(client.post('/login', { email, password })),

  getModels: () => request(client.get('/models')),

  generate: (payload) =>
    request(client.post('/generate', payload, { timeout: GENERATE_TIMEOUT })),

  getHistory: (page = 1, limit = 20) =>
    request(client.get('/history', { params: { page, limit } })),

  getGeneration: (id) => request(client.get(`/history/${id}`)),

  deleteGeneration: (id) => request(client.delete(`/history/${id}`)),

  getProfile: () => request(client.get('/profile')),

  /** Fetches an authenticated image as a Blob (plain <img src> can't send headers). */
  getImageBlob: (imageUrl) =>
    client.get(imageUrl, { baseURL: BASE_URL.replace(/\/api\/v1$/, ''), responseType: 'blob' })
      .then((res) => URL.createObjectURL(res.data)),
}

export default client
