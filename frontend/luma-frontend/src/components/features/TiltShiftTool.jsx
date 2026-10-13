import { useEffect, useRef, useState } from 'react'
import { api } from '../../api/client'
import { useToast } from '../../context/ToastContext'
import ImageUploader, { ImageDropzone, useImagePicker } from './ImageUploader'

export default function TiltShiftTool() {
  const { showToast } = useToast()
  const [file, setFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState('')
  const [focusPosition, setFocusPosition] = useState(0.5)
  const [focusWidth, setFocusWidth] = useState(0.2)
  const [blurStrength, setBlurStrength] = useState(15)
  const [saturationBoost, setSaturationBoost] = useState(1.4)
  const [contrastBoost, setContrastBoost] = useState(1.2)
  const [loading, setLoading] = useState(false)
  const [resultUrl, setResultUrl] = useState('')

  const resultUrlRef = useRef('')
  useEffect(() => () => {
    if (resultUrlRef.current) URL.revokeObjectURL(resultUrlRef.current)
  }, [])

  function setResult(next) {
    if (resultUrlRef.current) URL.revokeObjectURL(resultUrlRef.current)
    resultUrlRef.current = next
    setResultUrl(next)
  }

  function handleImagePicked(picked, url) {
    setFile(picked)
    setPreviewUrl(url)
    setResult('')
  }
  const pickImage = useImagePicker(handleImagePicked)

  async function handleDone() {
    if (!file) return
    setLoading(true)
    try {
      const url = await api.processTiltShift(file, {
        focus_position: focusPosition,
        focus_width: focusWidth,
        blur_strength: blurStrength,
        saturation_boost: saturationBoost,
        contrast_boost: contrastBoost,
      })
      setResult(url)
      showToast('Tilt-Shift applied', 'success')
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
          <h2 className="spot-blur-title">Tilt-Shift</h2>
          <p className="spot-blur-sub">Upload an image to simulate a tilt-shift lens (miniature-model look).</p>
        </div>
        <ImageUploader file={file} onPick={pickImage} />
      </div>

      {!previewUrl && <ImageDropzone onPick={pickImage} />}

      {previewUrl && resultUrl && (
        <div className="result-image-wrap spot-blur-result">
          <img src={resultUrl} alt="Tilt-Shift result" />
        </div>
      )}

      {previewUrl && !resultUrl && (
        <div className="spot-blur-stage">
          <img src={previewUrl} alt="Uploaded image to tilt-shift" className="spot-blur-image" draggable={false} />
        </div>
      )}

      {previewUrl && (
        <div className="spot-blur-controls">
          {!resultUrl && (
            <div className="field-row">
              <div className="field">
                <label htmlFor="tilt-shift-focus-position">Focus position ({focusPosition.toFixed(2)})</label>
                <input id="tilt-shift-focus-position" type="range" min={0} max={1} step={0.01} value={focusPosition}
                  onChange={(e) => setFocusPosition(Number(e.target.value))} />
              </div>
              <div className="field">
                <label htmlFor="tilt-shift-focus-width">Focus width ({focusWidth.toFixed(2)})</label>
                <input id="tilt-shift-focus-width" type="range" min={0.05} max={0.8} step={0.01} value={focusWidth}
                  onChange={(e) => setFocusWidth(Number(e.target.value))} />
              </div>
              <div className="field">
                <label htmlFor="tilt-shift-blur">Blur strength ({blurStrength})</label>
                <input id="tilt-shift-blur" type="range" min={1} max={30} value={blurStrength}
                  onChange={(e) => setBlurStrength(Number(e.target.value))} />
              </div>
              <div className="field">
                <label htmlFor="tilt-shift-saturation">Saturation boost ({saturationBoost.toFixed(1)})</label>
                <input id="tilt-shift-saturation" type="range" min={1} max={2.5} step={0.1} value={saturationBoost}
                  onChange={(e) => setSaturationBoost(Number(e.target.value))} />
              </div>
              <div className="field">
                <label htmlFor="tilt-shift-contrast">Contrast boost ({contrastBoost.toFixed(1)})</label>
                <input id="tilt-shift-contrast" type="range" min={1} max={2} step={0.1} value={contrastBoost}
                  onChange={(e) => setContrastBoost(Number(e.target.value))} />
              </div>
            </div>
          )}

          <div className="action-row spot-blur-actions">
            {resultUrl ? (
              <>
                <button type="button" className="btn btn-ghost" onClick={() => setResult('')}>
                  Back to editing
                </button>
                <a className="btn btn-primary" href={resultUrl} download="tilt-shift.png">Download</a>
              </>
            ) : (
              <button type="button" className="btn btn-primary" onClick={handleDone} disabled={loading}>
                {loading ? <><span className="spinner" /> Processing…</> : 'Process'}
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
