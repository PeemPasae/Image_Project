const LEGACY_KEY = 'luma_settings'

export const DEFAULT_SETTINGS = {
  defaultModel: '',
  defaultWidth: 512,
  defaultHeight: 512,
  defaultSteps: 20,
  defaultCfgScale: 7,
  defaultSampler: 'DPM++ 2M Karras',
}

export function settingsKey(user) {
  if (!user || user.id == null) return null
  return `${LEGACY_KEY}_${user.id}`
}

// Moves the legacy shared key to this user's key once, then deletes it.
function migrateLegacy(key) {
  const legacy = localStorage.getItem(LEGACY_KEY)
  if (legacy === null) return
  if (localStorage.getItem(key) === null) localStorage.setItem(key, legacy)
  localStorage.removeItem(LEGACY_KEY)
}

export function loadSettings(user) {
  const key = settingsKey(user)
  if (!key) return { ...DEFAULT_SETTINGS }
  try {
    migrateLegacy(key)
    const raw = localStorage.getItem(key)
    return raw ? { ...DEFAULT_SETTINGS, ...JSON.parse(raw) } : { ...DEFAULT_SETTINGS }
  } catch {
    return { ...DEFAULT_SETTINGS }
  }
}

export function saveSettings(user, settings) {
  const key = settingsKey(user)
  if (!key) return false
  localStorage.setItem(key, JSON.stringify(settings))
  return true
}
