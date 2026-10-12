import { describe, it, expect, beforeEach } from 'vitest'
import { DEFAULT_SETTINGS, settingsKey, loadSettings, saveSettings } from '../utils/settingsStorage'

const A = { id: 1 }
const B = { id: 2 }

describe('settingsStorage', () => {
  beforeEach(() => localStorage.clear())

  it('gives different keys to different users', () => {
    expect(settingsKey(A)).toBe('luma_settings_1')
    expect(settingsKey(B)).toBe('luma_settings_2')
  })

  it('returns defaults and touches no key when there is no user', () => {
    expect(loadSettings(null)).toEqual(DEFAULT_SETTINGS)
    expect(saveSettings(null, { defaultSteps: 9 })).toBe(false)
    expect(localStorage.length).toBe(0)
  })

  it('keeps each user\'s settings isolated', () => {
    saveSettings(A, { ...DEFAULT_SETTINGS, defaultSteps: 30 })
    saveSettings(B, { ...DEFAULT_SETTINGS, defaultSteps: 10 })
    expect(loadSettings(A).defaultSteps).toBe(30)
    expect(loadSettings(B).defaultSteps).toBe(10)
    expect(loadSettings({ id: 3 })).toEqual(DEFAULT_SETTINGS)
  })

  it('migrates the legacy key once, to the first user only', () => {
    localStorage.setItem('luma_settings', JSON.stringify({ defaultSteps: 42 }))
    expect(loadSettings(A).defaultSteps).toBe(42)
    expect(localStorage.getItem('luma_settings')).toBeNull()
    expect(loadSettings(B)).toEqual(DEFAULT_SETTINGS)
    expect(loadSettings(A).defaultSteps).toBe(42)
  })

  it('does not overwrite an existing user key with the legacy value', () => {
    saveSettings(A, { ...DEFAULT_SETTINGS, defaultSteps: 5 })
    localStorage.setItem('luma_settings', JSON.stringify({ defaultSteps: 42 }))
    expect(loadSettings(A).defaultSteps).toBe(5)
    expect(localStorage.getItem('luma_settings')).toBeNull()
  })
})
