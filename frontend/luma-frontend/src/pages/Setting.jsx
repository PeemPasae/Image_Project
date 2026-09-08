import { useEffect, useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { useTheme } from '../context/ThemeContext'

const SAMPLERS = ['DPM++ 2M Karras', 'Euler a', 'Euler']
const SIZES = [512, 768, 1024]
const STORAGE_KEY = 'luma_settings'

const DEFAULT_SETTINGS = {
  defaultModel: '',
  defaultWidth: 512,
  defaultHeight: 512,
  defaultSteps: 20,
  defaultCfgScale: 7,
  defaultSampler: 'DPM++ 2M Karras',
}

export default function Setting() {
  const { logout } = useAuth()
  const { themeId, setThemeId, themes } = useTheme()
  const [settings, setSettings] = useState(DEFAULT_SETTINGS)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) setSettings({ ...DEFAULT_SETTINGS, ...JSON.parse(raw) })
  }, [])

  function update(key, value) {
    setSettings((s) => ({ ...s, [key]: value }))
    setSaved(false)
  }

  function handleSave(e) {
    e.preventDefault()
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings))
    setSaved(true)
    setTimeout(() => setSaved(false), 1800)
  }

  return (
    <div>
      <div className="page-header">
        <h1>Setting</h1>
        <p>Appearance is applied immediately. Generation defaults are stored locally in this browser.</p>
      </div>

      {/* ===== Appearance ===== */}
      <div className="card" style={{ marginBottom: 20 }}>
        <div style={{ fontWeight: 700, marginBottom: 14 }}>Appearance</div>
        <div className="field" style={{ maxWidth: 280 }}>
          <label htmlFor="theme">Theme</label>
          <select id="theme" value={themeId} onChange={(e) => setThemeId(e.target.value)}>
            {themes.map((t) => <option key={t.id} value={t.id}>{t.label}</option>)}
          </select>
        </div>
      </div>

      {/* ===== Generation Defaults ===== */}
      <form onSubmit={handleSave} className="card" style={{ marginBottom: 20 }}>
        <div style={{ fontWeight: 700, marginBottom: 14 }}>Generation Defaults</div>
        <div className="field-row">
          <div className="field">
            <label htmlFor="defaultWidth">Default Width</label>
            <select id="defaultWidth" value={settings.defaultWidth} onChange={(e) => update('defaultWidth', Number(e.target.value))}>
              {SIZES.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
          <div className="field">
            <label htmlFor="defaultHeight">Default Height</label>
            <select id="defaultHeight" value={settings.defaultHeight} onChange={(e) => update('defaultHeight', Number(e.target.value))}>
              {SIZES.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
        </div>
        <div className="field-row">
          <div className="field">
            <label htmlFor="defaultSteps">Default Steps</label>
            <input id="defaultSteps" type="number" min={1} max={50} value={settings.defaultSteps} onChange={(e) => update('defaultSteps', Number(e.target.value))} />
          </div>
          <div className="field">
            <label htmlFor="defaultCfgScale">Default CFG Scale</label>
            <input id="defaultCfgScale" type="number" min={1} max={20} step={0.5} value={settings.defaultCfgScale} onChange={(e) => update('defaultCfgScale', Number(e.target.value))} />
          </div>
        </div>
        <div className="field" style={{ maxWidth: 280 }}>
          <label htmlFor="defaultSampler">Default Sampler</label>
          <select id="defaultSampler" value={settings.defaultSampler} onChange={(e) => update('defaultSampler', e.target.value)}>
            {SAMPLERS.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
        <div className="action-row">
          <button className="btn btn-primary" type="submit">{saved ? 'Saved ✓' : 'Save Defaults'}</button>
        </div>
      </form>

      {/* ===== Account ===== */}
      <div className="card">
        <div style={{ fontWeight: 700, marginBottom: 14 }}>Account</div>
        <button type="button" className="btn btn-danger" onClick={logout}>Logout</button>
      </div>
    </div>
  )
}