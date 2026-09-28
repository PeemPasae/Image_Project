import { useEffect, useRef, useState } from 'react'
import { api } from '../../api/client'
import { useToast } from '../../context/ToastContext'
import ImageUploader, { ImageDropzone, useImagePicker } from './ImageUploader'

export default function CartoonizeTool() {
  const { showToast } = useToast()
  const [file, setFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState('')
  const [numColors, setNumColors] = useState(8)
  const [lineThickness, setLineThickness] = useState(2)
  const [smoothness, setSmoothness] = useState(5)
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
      const url = await api.processCartoonize(file, {
        num_colors: numColors, line_thickness: lineThickness, smoothness,
      })
      setResult(url)
      showToast('Cartoonize applied', 'success')
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
          <h2 className="spot-blur-title">Cartoonize</h2>
          <p className="spot-blur-sub">Upload an image to turn it into a cartoon/anime-style illustration.</p>
        </div>
        <ImageUploader file={file} onPick={pickImage} />
      </div>

      {!previewUrl && <ImageDropzone onPick={pickImage} />}

      {previewUrl && resultUrl && (
        <div className="result-image-wrap spot-blur-result">
          <img src={resultUrl} alt="Cartoonize result" />
        </div>
      )}

      {previewUrl && !resultUrl && (
        <div className="spot-blur-stage">
          <img src={previewUrl} alt="Uploaded image to cartoonize" className="spot-blur-image" draggable={false} />
        </div>
      )}

      {previewUrl && (
        <div className="spot-blur-controls">
          {!resultUrl && (
            <div className="field-row">
              <div className="field">
                <label htmlFor="cartoonize-colors">Number of colors ({numColors})</label>
                <input id="cartoonize-colors" type="range" min={4} max={32} value={numColors}
                  onChange={(e) => setNumColors(Number(e.target.value))} />
              </div>
              <div className="field">
                <label htmlFor="cartoonize-lines">Line thickness ({lineThickness})</label>
                <input id="cartoonize-lines" type="range" min={1} max={5} value={lineThickness}
                  onChange={(e) => setLineThickness(Number(e.target.value))} />
              </div>
              <div className="field">
                <label htmlFor="cartoonize-smoothness">Smoothness ({smoothness})</label>
                <input id="cartoonize-smoothness" type="range" min={1} max={10} value={smoothness}
                  onChange={(e) => setSmoothness(Number(e.target.value))} />
              </div>
            </div>
          )}

          <div className="action-row spot-blur-actions">
            {resultUrl ? (
              <>
                <button type="button" className="btn btn-ghost" onClick={() => setResult('')}>
                  Back to editing
                </button>
                <a className="btn btn-primary" href={resultUrl} download="cartoonize.png">Download</a>
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
