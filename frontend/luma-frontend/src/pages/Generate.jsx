import { useEffect, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { api } from '../api/client'

const SAMPLERS = ['DPM++ 2M Karras', 'Euler a', 'Euler']
const SIZES = [512, 768, 1024]

const DEFAULTS = {
  prompt: '',
  negative_prompt: '',
  checkpoint: '',
  width: 512,
  height: 512,
  steps: 20,
  cfg_scale: 7,
  sampler: 'DPM++ 2M Karras',
  seed: -1,
}

export default function Generate() {
  const navigate = useNavigate()
  const location = useLocation()
  const [form, setForm] = useState({ ...DEFAULTS, ...(location.state?.prefill || {}) })
  const [models, setModels] = useState([])
  const [useRandomSeed, setUseRandomSeed] = useState(form.seed === -1)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    api.getModels()
      .then((data) => {
        setModels(data.models)
        if (!form.checkpoint && data.models[0]) {
          setForm((f) => ({ ...f, checkpoint: data.models[0].model_name }))
        }
      })
      .catch(() => setModels([]))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  function update(key, value) {
    setForm((f) => ({ ...f, [key]: value }))
  }

  function validate() {
    if (!form.prompt.trim()) return 'Prompt is required'
    if (form.prompt.length > 2000) return 'Prompt must be 2000 characters or fewer'
    if (form.negative_prompt.length > 2000) return 'Negative prompt must be 2000 characters or fewer'
    if (!SIZES.includes(Number(form.width)) || !SIZES.includes(Number(form.height))) return 'Width/height must be 512, 768, or 1024'
    if (form.steps < 1 || form.steps > 50) return 'Steps must be between 1 and 50'
    if (form.cfg_scale < 1 || form.cfg_scale > 20) return 'CFG scale must be between 1 and 20'
    if (!SAMPLERS.includes(form.sampler)) return 'Invalid sampler'
    return null
  }

  async function handleSubmit(e) {
    e.preventDefault()
    const validationError = validate()
    if (validationError) {
      setError(validationError)
      return
    }
    setError('')
    setLoading(true)
    try {
      const payload = {
        ...form,
        width: Number(form.width),
        height: Number(form.height),
        steps: Number(form.steps),
        cfg_scale: Number(form.cfg_scale),
        seed: useRandomSeed ? -1 : Number(form.seed),
      }
      const data = await api.generate(payload)
      navigate(`/result/${data.generation_id}`)
    } catch (err) {
      if (err.code === 'AI_SERVER_BUSY') {
        setError('The AI server is busy with another generation. Try again in a moment.')
      } else if (err.code === 'AI_SERVER_TIMEOUT') {
        setError('The AI server took too long to respond. Try again.')
      } else {
        setError(err.message)
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1>Generate</h1>
        <p>Describe what you want to see.</p>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <form onSubmit={handleSubmit} className="two-col">
        <div>
          <div className="field">
            <label htmlFor="prompt">Prompt</label>
            <textarea id="prompt" rows={4} maxLength={2000} value={form.prompt}
              onChange={(e) => update('prompt', e.target.value)}
              placeholder="A beautiful girl standing in a cyberpunk city, neon lights, cinematic lighting" />
          </div>
          <div className="field">
            <label htmlFor="negative_prompt">Negative Prompt</label>
            <textarea id="negative_prompt" rows={2} maxLength={2000} value={form.negative_prompt}
              onChange={(e) => update('negative_prompt', e.target.value)}
              placeholder="blurry, low quality, bad anatomy" />
          </div>
          <div className="field">
            <label htmlFor="checkpoint">Model / Checkpoint</label>
            <select id="checkpoint" value={form.checkpoint} onChange={(e) => update('checkpoint', e.target.value)}>
              {models.map((m) => <option key={m.model_name} value={m.model_name}>{m.title}</option>)}
            </select>
          </div>

          <div className="field-row">
            <div className="field">
              <label htmlFor="width">Width</label>
              <select id="width" value={form.width} onChange={(e) => update('width', e.target.value)}>
                {SIZES.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
            <div className="field">
              <label htmlFor="height">Height</label>
              <select id="height" value={form.height} onChange={(e) => update('height', e.target.value)}>
                {SIZES.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
          </div>

          <div className="field-row">
            <div className="field">
              <label htmlFor="steps">Sampling Steps ({form.steps})</label>
              <input id="steps" type="range" min={1} max={50} value={form.steps} onChange={(e) => update('steps', Number(e.target.value))} />
            </div>
            <div className="field">
              <label htmlFor="cfg_scale">CFG Scale ({form.cfg_scale})</label>
              <input id="cfg_scale" type="range" min={1} max={20} step={0.5} value={form.cfg_scale} onChange={(e) => update('cfg_scale', Number(e.target.value))} />
            </div>
          </div>

          <div className="field">
            <label htmlFor="sampler">Sampler</label>
            <select id="sampler" value={form.sampler} onChange={(e) => update('sampler', e.target.value)}>
              {SAMPLERS.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>

          <div className="field">
            <label>
              <input type="checkbox" checked={useRandomSeed} onChange={(e) => setUseRandomSeed(e.target.checked)} style={{ marginRight: 8 }} />
              Random seed
            </label>
            {!useRandomSeed && (
              <input type="number" min={0} max={2147483647} value={form.seed === -1 ? '' : form.seed}
                onChange={(e) => update('seed', e.target.value)} placeholder="Custom seed" style={{ marginTop: 8 }} />
            )}
          </div>

          <button className="btn btn-primary" type="submit" disabled={loading} style={{ width: '100%' }}>
            {loading ? <><span className="spinner" /> Generating…</> : 'Generate'}
          </button>
        </div>

        <div className="card">
          <div style={{ fontWeight: 700, marginBottom: 10 }}>Tips</div>
          <ul style={{ fontSize: 12.5, color: 'var(--text-dim)', paddingLeft: 18, display: 'flex', flexDirection: 'column', gap: 8 }}>
            <li>Be specific about subject, style, and lighting.</li>
            <li>Use the negative prompt to steer away from artifacts.</li>
            <li>Generation can take 10–60+ seconds — the button stays disabled while it runs.</li>
          </ul>
        </div>
      </form>
    </div>
  )
}
