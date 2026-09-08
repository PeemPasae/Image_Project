import { createContext, useContext, useEffect, useState } from 'react'
import { THEME_PRESETS, DEFAULT_THEME_ID, getThemeById } from '../themes/presets'

const ThemeContext = createContext(null)

function cssVarName(key) {
  return key.replace(/([A-Z])/g, '-$1').toLowerCase()
}

export function ThemeProvider({ children }) {
  const [themeId, setThemeId] = useState(() => localStorage.getItem('luma_theme') || DEFAULT_THEME_ID)

  useEffect(() => {
    const theme = getThemeById(themeId)
    const root = document.documentElement
    Object.entries(theme.colors).forEach(([key, value]) => {
      root.style.setProperty(`--${cssVarName(key)}`, value)
    })
    localStorage.setItem('luma_theme', themeId)
  }, [themeId])

  const value = { themeId, setThemeId, themes: THEME_PRESETS }
  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}

export function useTheme() {
  const ctx = useContext(ThemeContext)
  if (!ctx) throw new Error('useTheme must be used within ThemeProvider')
  return ctx
}