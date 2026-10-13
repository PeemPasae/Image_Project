import { useState } from 'react'
import { api, MOCK_MODE } from '../../api/client'
import { useToast } from '../../context/ToastContext'
import ImageUploader, { ImageDropzone, useImagePicker } from './ImageUploader'

// User-facing text for the error codes the backend can return from
// /process/gesture (see backend_ref .../image_filters/routes.py). Anything
// else falls back to err.message (network errors, unexpected codes, etc.).
const GESTURE_ERROR_MESSAGES = {
  VALIDATION_ERROR: 'ข้อมูลที่ส่งไม่ถูกต้อง กรุณาตรวจสอบค่าที่ตั้งไว้',
  UNSUPPORTED_FILE_TYPE: 'รองรับเฉพาะไฟล์ .jpg, .jpeg, .png, .webp',
  INVALID_IMAGE: 'ไฟล์ภาพเสียหาย ไม่สามารถอ่านได้',
  UNAUTHORIZED: 'เซสชันหมดอายุ กรุณาเข้าสู่ระบบใหม่',
  MODEL_UNAVAILABLE: 'บริการรู้จำท่ามือยังไม่พร้อม ลองใหม่ภายหลัง',
}
function gestureErrorMessage(err) {
  return GESTURE_ERROR_MESSAGES[err.code] || err.message
}

export default function HandGestureTool() {
  const { showToast } = useToast()
  const [file, setFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState('')
  const [numHands, setNumHands] = useState(2)
  const [minConfidence, setMinConfidence] = useState(0.5)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  function handleImagePicked(picked, url) {
    setFile(picked)
    setPreviewUrl(url)
    setResult(null)
  }
  const pickImage = useImagePicker(handleImagePicked)

  async function handleRecognize() {
    if (!file) return
    setLoading(true)
    try {
      const data = await api.processGesture(file, { num_hands: numHands, min_confidence: minConfidence })
      setResult(data)
    } catch (err) {
      showToast(gestureErrorMessage(err), 'error')
    } finally {
      setLoading(false)
    }
  }

  // Contract: found can be false, and even when true `gesture` itself may in
  // principle be null — gesture_th is the only field guaranteed to always be
  // a display-ready string ("ไม่พบมือในภาพ" when nothing was recognized).
  const recognized = !!(result && result.found && result.gesture != null)

  return (
    <div className="spot-blur">
      <div className="spot-blur-head">
        <div>
          <h2 className="spot-blur-title">Hand Gesture</h2>
          <p className="spot-blur-sub">Upload an image to recognize a hand gesture.</p>
        </div>
        <ImageUploader file={file} onPick={pickImage} />
      </div>

      {!previewUrl && <ImageDropzone onPick={pickImage} />}

      {previewUrl && (
        <div className="spot-blur-stage">
          <img src={previewUrl} alt="Uploaded image for hand gesture recognition" className="spot-blur-image" draggable={false} />
        </div>
      )}

      {previewUrl && (
        <div className="spot-blur-controls">
          <div className="field-row">
            <div className="field">
              <label htmlFor="gesture-num-hands">Max hands ({numHands})</label>
              <input id="gesture-num-hands" type="range" min={1} max={4} value={numHands}
                onChange={(e) => setNumHands(Number(e.target.value))} />
            </div>
            <div className="field">
              <label htmlFor="gesture-min-confidence">Min confidence ({minConfidence.toFixed(1)})</label>
              <input id="gesture-min-confidence" type="range" min={0.1} max={1} step={0.1} value={minConfidence}
                onChange={(e) => setMinConfidence(Number(e.target.value))} />
            </div>
          </div>

          {result && (
            <div className="gesture-result card">
              {MOCK_MODE && <span className="gesture-mock-badge">ผลจำลอง</span>}
              {recognized ? (
                <>
                  <div className="gesture-result-name">{result.gesture_th}</div>
                  <div className="gesture-result-meta">
                    <span>{result.confidence.toFixed(1)}% confidence</span>
                    <span>{result.hand_count} hand{result.hand_count === 1 ? '' : 's'}</span>
                    <span>{result.inference_time_ms.toFixed(1)} ms</span>
                  </div>
                </>
              ) : (
                <div className="gesture-result-name">{result.gesture_th || 'ไม่พบมือในภาพ'}</div>
              )}
            </div>
          )}

          <div className="action-row spot-blur-actions">
            <button type="button" className="btn btn-primary" onClick={handleRecognize} disabled={loading}>
              {loading ? <><span className="spinner" /> Recognizing…</> : 'Recognize'}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
