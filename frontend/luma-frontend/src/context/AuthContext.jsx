import { createContext, useContext, useEffect, useState } from 'react'
import { api } from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('luma_token'))
  const [user, setUser] = useState(() => {
    const raw = localStorage.getItem('luma_user')
    return raw ? JSON.parse(raw) : null
  })
  const [ready, setReady] = useState(true) // token expiry is enforced server-side (401 -> logout)

  useEffect(() => {
    setReady(true)
  }, [])

  function persist(newToken, newUser) {
    localStorage.setItem('luma_token', newToken)
    localStorage.setItem('luma_user', JSON.stringify(newUser))
    setToken(newToken)
    setUser(newUser)
  }

  async function login(email, password) {
    const data = await api.login(email, password)
    persist(data.access_token, data.user)
    return data
  }

  async function register(email, password) {
    return api.register(email, password)
  }

  function logout() {
    localStorage.removeItem('luma_token')
    localStorage.removeItem('luma_user')
    setToken(null)
    setUser(null)
  }

  const value = {
    token,
    user,
    isAuthenticated: !!token,
    ready,
    login,
    register,
    logout,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
