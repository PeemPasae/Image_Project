import { useEffect, useRef, useState } from 'react'
import { api } from '../../api/client'
import { useToast } from '../../context/ToastContext'
import SpotBlurCanvas from './SpotBlurCanvas'

const ACCEPTED_TYPES = ['image/jpeg', 'image/png', 'image/webp']

export default function SpotBlurTool() {
  const { showToast } = useToast()
  const [file, setFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState('')
  const [circles, setCircles] = useState([])
  const [strength, setStrength] = useState(15)
  const [brushRadius, setBrushRadius] = useState(30)
  const [loading, setLoading] = useState(false)
  const [resultUrl, setResultUrl] = useState('')

  // Revoke object URLs when they're replaced and on unmount.
  const urls = useRef({ preview: '', result: '' })
  useEffect(() => () => {
    if (urls.current.preview) URL.revokeObjectURL(urls.current.preview)
    if (urls.current.result) URL.revokeObjectURL(urls.current.result)
  }, [])

  function replaceUrl(key, next, setter) {
    if (urls.current[key]) URL.revokeObjectURL(urls.current[key])
    urls.current[key] = next
    setter(next)
  }

  function handleFileChange(e) {
    const picked = e.target.files?.[0]
    e.target.value = '' // allow re-picking the same file
    if (!picked) return
    if (!ACCEPTED_TYPES.includes(picked.type)) {
      showToast('Please upload a JPG, PNG, or WEBP image.', 'error')
      return
    }
    setFile(picked)
    setCircles([])
    replaceUrl('result', '', setResultUrl)
    replaceUrl('preview', URL.createObjectURL(picked), setPreviewUrl)
  }

  async function handleDone() {
    if (!file) return
    if (circles.length === 0) {
      showToast('Paint at least one area first.', 'error')
      return
    }
    setLoading(true)
    try {
      // Contract wants [[x, y, radius], ...] as integers in natural-image pixels.
      const payload = circles.map((c) => [Math.round(c.x), Math.round(c.y), Math.max(1, Math.round(c.r))])
      const url = await api.processSpotBlur(file, payload, strength, true)
      replaceUrl('result', url, setResultUrl)
      showToast('Blur applied', 'success')
    } catch (err) {
      showToast(err.message, 'error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="spot-blur">
      <div className="spot-blur-head">
        <div>
          <h2 className="spot-blur-title">Spot Blur</h2>
          <p className="spot-blur-sub">Upload an image, then click and drag over the areas you want blurred.</p>
        </div>
        <label className="btn btn-ghost spot-blur-file">
          {file ? 'Change image' : 'Choose image'}
          <input type="file" accept={ACCEPTED_TYPES.join(',')} onChange={handleFileChange} hidden />
        </label>
      </div>

      {!previewUrl && (
        <div className="spot-blur-empty">No image yet — JPG, PNG, or WEBP.</div>
      )}

      {previewUrl && resultUrl && (
        <div className="result-image-wrap spot-blur-result">
          <img src={resultUrl} alt="Spot blur result" />
        </div>
      )}

      {previewUrl && !resultUrl && (
        <SpotBlurCanvas src={previewUrl} circles={circles} onChange={setCircles} brushRadius={brushRadius} />
      )}

      {previewUrl && (
        <div className="spot-blur-controls">
          {!resultUrl && (
            <div className="field-row">
              <div className="field">
                <label htmlFor="spot-blur-strength">Blur strength ({strength})</label>
                <input id="spot-blur-strength" type="range" min={1} max={30} value={strength}
                  onChange={(e) => setStrength(Number(e.target.value))} />
              </div>
              <div className="field">
                <label htmlFor="spot-blur-brush">Brush radius ({brushRadius}px)</label>
                <input id="spot-blur-brush" type="range" min={5} max={100} value={brushRadius}
                  onChange={(e) => setBrushRadius(Number(e.target.value))} />
              </div>
            </div>
          )}

          <div className="action-row spot-blur-actions">
            {resultUrl ? (
              <>
                <button type="button" className="btn btn-ghost" onClick={() => replaceUrl('result', '', setResultUrl)}>
                  Back to editing
                </button>
                <a className="btn btn-primary" href={resultUrl} download="spot-blur.png">Download</a>
              </>
            ) : (
              <>
                <span className="spot-blur-count">{circles.length} spot{circles.length === 1 ? '' : 's'} painted</span>
                <button type="button" className="btn btn-ghost" onClick={() => setCircles([])}
                  disabled={loading || circles.length === 0}>
                  Clear all
                </button>
                <button type="button" className="btn btn-primary" onClick={handleDone} disabled={loading}>
                  {loading ? <><span className="spinner" /> Processing…</> : 'Done'}
                </button>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
