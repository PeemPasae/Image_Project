import { useEffect, useRef, useState } from 'react'
import { api } from '../../api/client'
import { useToast } from '../../context/ToastContext'
import ImageUploader, { ImageDropzone, useImagePicker } from './ImageUploader'

export default function HdrEnhancerTool() {
  const { showToast } = useToast()
  const [file, setFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState('')
  const [clipLimit, setClipLimit] = useState(3.0)
  const [gridSize, setGridSize] = useState(8)
  const [detailStrength, setDetailStrength] = useState(1.5)
  const [colorBalance, setColorBalance] = useState(true)
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
      const url = await api.processHdrEnhancer(file, {
        clahe_clip_limit: clipLimit,
        clahe_grid_size: gridSize,
        detail_strength: detailStrength,
        color_balance: colorBalance,
      })
      setResult(url)
      showToast('HDR Enhancer applied', 'success')
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
          <h2 className="spot-blur-title">HDR Enhancer</h2>
          <p className="spot-blur-sub">Upload an image to boost detail and contrast, HDR-style, using CLAHE.</p>
        </div>
        <ImageUploader file={file} onPick={pickImage} />
      </div>

      {!previewUrl && <ImageDropzone onPick={pickImage} />}

      {previewUrl && resultUrl && (
        <div className="result-image-wrap spot-blur-result">
          <img src={resultUrl} alt="HDR Enhancer result" />
        </div>
      )}

      {previewUrl && !resultUrl && (
        <div className="spot-blur-stage">
          <img src={previewUrl} alt="Uploaded image to enhance" className="spot-blur-image" draggable={false} />
        </div>
      )}

      {previewUrl && (
        <div className="spot-blur-controls">
          {!resultUrl && (
            <div className="field-row">
              <div className="field">
                <label htmlFor="hdr-clip-limit">CLAHE clip limit ({clipLimit.toFixed(1)})</label>
                <input id="hdr-clip-limit" type="range" min={1} max={5} step={0.1} value={clipLimit}
                  onChange={(e) => setClipLimit(Number(e.target.value))} />
              </div>
              <div className="field">
                <label htmlFor="hdr-grid-size">CLAHE grid size ({gridSize})</label>
                <input id="hdr-grid-size" type="range" min={2} max={16} value={gridSize}
                  onChange={(e) => setGridSize(Number(e.target.value))} />
              </div>
              <div className="field">
                <label htmlFor="hdr-detail">Detail strength ({detailStrength.toFixed(1)})</label>
                <input id="hdr-detail" type="range" min={0} max={3} step={0.1} value={detailStrength}
                  onChange={(e) => setDetailStrength(Number(e.target.value))} />
              </div>
              <div className="field">
                <label>
                  <input type="checkbox" checked={colorBalance} onChange={(e) => setColorBalance(e.target.checked)} style={{ marginRight: 8 }} />
                  Color balance
                </label>
              </div>
            </div>
          )}

          <div className="action-row spot-blur-actions">
            {resultUrl ? (
              <>
                <button type="button" className="btn btn-ghost" onClick={() => setResult('')}>
                  Back to editing
                </button>
                <a className="btn btn-primary" href={resultUrl} download="hdr-enhancer.png">Download</a>
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
