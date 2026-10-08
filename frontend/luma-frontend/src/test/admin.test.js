import { describe, it, expect, beforeEach, vi } from 'vitest'
import { isAdmin } from '../utils/roles'
import { visibleNavItems } from '../components/templates/navItems'

describe('role checks', () => {
  it('only role "admin" is admin', () => {
    expect(isAdmin({ id: 1, role: 'admin' })).toBe(true)
    expect(isAdmin({ id: 1, role: 'user' })).toBe(false)
    expect(isAdmin({ id: 1 })).toBe(false)
    expect(isAdmin(null)).toBe(false)
  })

  it('shows the Admin menu to admins only', () => {
    const labels = (u) => visibleNavItems(u).map((i) => i.label)
    expect(labels({ role: 'admin' })).toContain('Admin')
    expect(labels({ role: 'user' })).not.toContain('Admin')
    expect(labels(null)).not.toContain('Admin')
  })
})

describe('admin mock API', () => {
  let api
  beforeEach(async () => {
    vi.resetModules()
    vi.stubEnv('VITE_MOCK_MODE', 'true')
    ;({ api } = await import('../api/client'))
  })

  it('lists at least 5 users including the mock admin', async () => {
    const { users } = await api.getAdminUsers()
    expect(users.length).toBeGreaterThanOrEqual(5)
    expect(users[0]).toHaveProperty('generation_count')
  })

  it('removes a deleted user for the rest of the session', async () => {
    await api.deleteAdminUser(2)
    const { users } = await api.getAdminUsers()
    expect(users.find((u) => u.id === 2)).toBeUndefined()
  })

  it('gives the mock login user role admin without touching other mocks', async () => {
    const login = await api.login('a@a.com', 'x')
    expect(login.user.role).toBe('admin')
    expect((await api.getModels()).models.length).toBeGreaterThan(0)
  })
})
