import { useEffect, useRef, useState } from 'react'
import { api } from '../../api/client'
import { useToast } from '../../context/ToastContext'
import ImageUploader, { ImageDropzone, useImagePicker } from './ImageUploader'
import RemoveBackgroundCanvas from './RemoveBackgroundCanvas'

// User-facing text for the error codes /process/remove-bg can return.
const REMOVE_BG_ERROR_MESSAGES = {
  VALIDATION_ERROR: 'ข้อมูลที่ส่งไม่ถูกต้อง กรุณาตรวจสอบค่าที่ตั้งไว้',
  UNSUPPORTED_FILE_TYPE: 'รองรับเฉพาะไฟล์ .jpg, .jpeg, .png, .webp',
  INVALID_IMAGE: 'ไฟล์ภาพเสียหาย ไม่สามารถอ่านได้',
  MODEL_UNAVAILABLE: 'บริการลบพื้นหลังยังไม่พร้อม ลองใหม่ภายหลัง',
  GENERATION_FAILED: 'ลบพื้นหลังไม่สำเร็จ กรุณาลองใหม่',
  UNAUTHORIZED: 'เซสชันหมดอายุ กรุณาเข้าสู่ระบบใหม่',
}
function removeBgErrorMessage(err) {
  return REMOVE_BG_ERROR_MESSAGES[err.code] || err.message
}

// Mirrors the backend's own mode-selection rule (confirmed, not guessed):
// no rect/strokes at all -> pure AI; use_ai=false -> pure GrabCut (rect
// required); anything else (rect and/or strokes present, AI still on) -> both.
function modeLabel(rect, strokes, useAi) {
  if (!useAi) return 'GrabCut ล้วน'
  if (!rect && strokes.length === 0) return 'AI อัตโนมัติ'
  return 'AI + GrabCut'
}

const MAX_STROKES = 200
const MAX_POINTS = 5000

export default function RemoveBackgroundTool() {
  const { showToast } = useToast()
  const [file, setFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState('')
  const [editorState, setEditorState] = useState({ rect: null, strokes: [], useAi: true })
  const [loading, setLoading] = useState(false)
  const [resultUrl, setResultUrl] = useState('')
  const [resultMeta, setResultMeta] = useState(null)

  // ImageUploader owns the preview URL's lifecycle; this only needs to revoke
  // the processed result URL (replaced or left behind on unmount).
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
    setEditorState({ rect: null, strokes: [], useAi: true })
    setResult('')
    setResultMeta(null)
  }
  const pickImage = useImagePicker(handleImagePicked)

  const { rect, strokes, useAi } = editorState
  const canSubmit = useAi || !!rect

  async function handleRemoveBackground() {
    if (!file || !canSubmit) return
    const strokeCount = strokes.length
    const pointCount = strokes.reduce((sum, s) => sum + s.points.length, 0)
    if (strokeCount > MAX_STROKES || pointCount > MAX_POINTS) {
      showToast(`วาดได้สูงสุด ${MAX_STROKES} เส้น รวมไม่เกิน ${MAX_POINTS} จุด (ตอนนี้ ${strokeCount} เส้น, ${pointCount} จุด)`, 'error')
      return
    }
    setLoading(true)
    const label = modeLabel(rect, strokes, useAi)
    const start = performance.now()
    try {
      const url = await api.processRemoveBackground(file, {
        rect: rect ?? undefined,
        strokes: strokes.length ? strokes : undefined,
        use_ai: useAi,
      })
      const elapsedMs = performance.now() - start
      setResult(url)
      setResultMeta({ label, elapsedMs })
      showToast('Background removed', 'success')
    } catch (err) {
      showToast(removeBgErrorMessage(err), 'error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="spot-blur">
      <div className="spot-blur-head">
        <div>
          <h2 className="spot-blur-title">Remove Background</h2>
          <p className="spot-blur-sub">Upload an image to remove its background automatically.</p>
        </div>
        <ImageUploader file={file} onPick={pickImage} />
      </div>

      {!previewUrl && <ImageDropzone onPick={pickImage} />}

      {previewUrl && resultUrl && (
        <>
          <div className="result-image-wrap spot-blur-result remove-bg-result">
            <img src={resultUrl} alt="Background removed result" />
          </div>
          {resultMeta && (
            <div className="rb-result-meta card">
              <span>{resultMeta.label}</span>
              <span>{resultMeta.elapsedMs.toFixed(0)} ms</span>
            </div>
          )}
        </>
      )}

      {previewUrl && !resultUrl && (
        <RemoveBackgroundCanvas src={previewUrl} onChange={setEditorState} />
      )}

      {previewUrl && (
        <div className="spot-blur-controls">
          <div className="action-row spot-blur-actions">
            {resultUrl ? (
              <>
                <button type="button" className="btn btn-ghost" onClick={() => setResult('')}>
                  Back to editing
                </button>
                <a className="btn btn-primary" href={resultUrl} download="remove-background.png">Download</a>
              </>
            ) : (
              <>
                {!canSubmit && (
                  <span className="rb-disabled-hint">ปิดใช้ AI ต้องลากกรอบอย่างน้อย 1 กรอบก่อนจึงจะกดลบพื้นหลังได้</span>
                )}
                <button type="button" className="btn btn-primary" onClick={handleRemoveBackground} disabled={loading || !canSubmit}>
                  {loading ? <><span className="spinner" /> กำลังลบพื้นหลัง…</> : 'ลบพื้นหลัง'}
                </button>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
