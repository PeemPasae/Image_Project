import { useCallback, useEffect, useRef, useState } from 'react'

// Same look as SpotBlurTool's controls; self-contained editor (mode buttons,
// brush size, AI toggle, undo/reset) since RemoveBackgroundTool only needs
// the derived { rect, strokes, useAi } out of it, not the drawing UI itself.
const MODES = [
  { id: 'rect', label: 'ลากกรอบ' },
  { id: 'keep', label: 'แปรงเก็บ' },
  { id: 'remove', label: 'แปรงลบ' },
]

let nextActionId = 0

function pointXY(p) {
  return Array.isArray(p) ? p : [p.x, p.y]
}

/**
 * Image + absolutely-positioned <canvas> overlay, same natural-pixel-space
 * approach as SpotBlurCanvas.jsx (naturalWidth/clientWidth scale factor —
 * the image is usually displayed smaller than its natural size).
 *
 * Unlike SpotBlurCanvas (a flat `circles` array), the backend contract here
 * wants ONE `rect` plus an ordered `strokes` array, and undo must remove
 * whichever (rect or stroke) was drawn most recently — so both are kept in
 * a single chronological `actions` stack and `rect`/`strokes` are derived
 * from it on every render.
 */
export default function RemoveBackgroundCanvas({ src, onChange }) {
  const imgRef = useRef(null)
  const canvasRef = useRef(null)
  const painting = useRef(false)

  // in-progress (uncommitted) drag state — not lifted to React state so a
  // drag doesn't spam commits; redraw() is called directly on every move
  const dragStartRef = useRef(null)
  const liveRectRef = useRef(null)
  const currentStrokeRef = useRef(null)
  const lastPointRef = useRef(null)

  const [mode, setMode] = useState('rect')
  const [brushRadius, setBrushRadius] = useState(30)
  const [useAi, setUseAi] = useState(true)
  const [actions, setActions] = useState([])

  const actionsRef = useRef(actions)
  actionsRef.current = actions

  const rect = [...actions].reverse().find((a) => a.type === 'rect')?.rect ?? null
  const strokes = actions.filter((a) => a.type === 'stroke').map((a) => a.stroke)

  useEffect(() => {
    onChange?.({ rect, strokes, useAi })
    // rect/strokes are derived fresh from `actions` every render — depending
    // on `actions` covers both, and including the derived values themselves
    // would just refire this on every render for no reason.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [actions, useAi])

  function getScale() {
    const img = imgRef.current
    if (!img || !img.clientWidth || !img.clientHeight) return null
    return {
      x: img.naturalWidth / img.clientWidth,
      y: img.naturalHeight / img.clientHeight,
    }
  }

  const redraw = useCallback(() => {
    const img = imgRef.current
    const canvas = canvasRef.current
    if (!img || !canvas) return
    const w = img.clientWidth
    const h = img.clientHeight
    const dpr = window.devicePixelRatio || 1
    if (canvas.width !== Math.round(w * dpr) || canvas.height !== Math.round(h * dpr)) {
      canvas.width = Math.round(w * dpr)
      canvas.height = Math.round(h * dpr)
    }
    canvas.style.width = `${w}px`
    canvas.style.height = `${h}px`

    const ctx = canvas.getContext('2d')
    if (!ctx) return
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    ctx.clearRect(0, 0, w, h)
    const scale = getScale()
    if (!scale) return

    // Colors read from the canvas's own computed style (set via CSS custom
    // properties in features.css) so nothing here is hardcoded — same
    // technique SpotBlurCanvas uses for its single overlay color.
    const cs = getComputedStyle(canvas)
    const rectColor = cs.getPropertyValue('--rb-rect').trim()
    const keepColor = cs.getPropertyValue('--rb-keep').trim()
    const removeColor = cs.getPropertyValue('--rb-remove').trim()

    function drawRect(r, color) {
      ctx.strokeStyle = color
      ctx.lineWidth = 2
      ctx.setLineDash([6, 4])
      ctx.strokeRect(r[0] / scale.x, r[1] / scale.y, r[2] / scale.x, r[3] / scale.y)
      ctx.setLineDash([])
    }
    function drawStroke(stroke, color) {
      ctx.fillStyle = color
      for (const p of stroke.points) {
        const [x, y] = pointXY(p)
        ctx.beginPath()
        ctx.arc(x / scale.x, y / scale.y, stroke.r / scale.x, 0, Math.PI * 2)
        ctx.fill()
      }
    }

    for (const a of actionsRef.current) {
      if (a.type === 'rect') drawRect(a.rect, rectColor)
      else drawStroke(a.stroke, a.stroke.type === 'keep' ? keepColor : removeColor)
    }
    if (liveRectRef.current) drawRect(liveRectRef.current, rectColor)
    if (currentStrokeRef.current) {
      drawStroke(currentStrokeRef.current, currentStrokeRef.current.type === 'keep' ? keepColor : removeColor)
    }
  }, [])

  useEffect(() => { redraw() }, [actions, redraw])

  // Keep the overlay matched to the displayed image size (window resize, sidebar, etc.).
  useEffect(() => {
    const img = imgRef.current
    if (!img || typeof ResizeObserver === 'undefined') return
    const ro = new ResizeObserver(() => redraw())
    ro.observe(img)
    return () => ro.disconnect()
  }, [redraw])

  function toNatural(e) {
    const scale = getScale()
    if (!scale) return null
    const box = canvasRef.current.getBoundingClientRect()
    return {
      x: (e.clientX - box.left) * scale.x,
      y: (e.clientY - box.top) * scale.y,
    }
  }

  function handlePointerDown(e) {
    if (e.button !== undefined && e.button !== 0) return
    const p = toNatural(e)
    if (!p) return
    e.preventDefault()
    painting.current = true
    if (mode === 'rect') {
      dragStartRef.current = p
      liveRectRef.current = [p.x, p.y, 0, 0]
    } else {
      const scale = getScale()
      currentStrokeRef.current = { type: mode, r: brushRadius * (scale?.x ?? 1), points: [[p.x, p.y]] }
      lastPointRef.current = p
    }
    redraw()
  }

  function handlePointerMove(e) {
    if (!painting.current) return
    const p = toNatural(e)
    if (!p) return
    if (mode === 'rect') {
      const start = dragStartRef.current
      if (!start) return
      liveRectRef.current = [
        Math.min(start.x, p.x),
        Math.min(start.y, p.y),
        Math.abs(p.x - start.x),
        Math.abs(p.y - start.y),
      ]
      redraw()
    } else {
      const stroke = currentStrokeRef.current
      const last = lastPointRef.current
      if (!stroke || !last) return
      // Only add a point once the cursor has travelled ~r/3 — continuous
      // stroke without flooding `points` with near-duplicates (same
      // threshold SpotBlurCanvas uses for its circles).
      if (Math.hypot(p.x - last.x, p.y - last.y) > stroke.r / 3) {
        stroke.points.push([p.x, p.y])
        lastPointRef.current = p
        redraw()
      }
    }
  }

  function commitPendingAction() {
    if (mode === 'rect') {
      const r = liveRectRef.current
      if (r && r[2] > 0 && r[3] > 0) {
        const rounded = r.map((v) => Math.round(v))
        setActions((prev) => [...prev, { id: nextActionId++, type: 'rect', rect: rounded }])
      }
    } else {
      const stroke = currentStrokeRef.current
      if (stroke && stroke.points.length > 0) {
        setActions((prev) => [...prev, {
          id: nextActionId++,
          type: 'stroke',
          stroke: {
            type: stroke.type,
            r: Math.max(1, Math.round(stroke.r)),
            points: stroke.points.map((p) => { const [x, y] = pointXY(p); return [Math.round(x), Math.round(y)] }),
          },
        }])
      }
    }
    dragStartRef.current = null
    liveRectRef.current = null
    currentStrokeRef.current = null
    lastPointRef.current = null
  }

  function stopPainting() {
    if (painting.current) commitPendingAction()
    painting.current = false
    redraw()
  }

  function handleUndo() {
    setActions((prev) => prev.slice(0, -1))
  }
  function handleReset() {
    setActions([])
  }

  return (
    <div className="rb-editor">
      <div className="rb-toolbar">
        <div className="rb-mode-group" role="radiogroup" aria-label="วิธีเลือกพื้นที่">
          {MODES.map((m) => (
            <button
              key={m.id}
              type="button"
              className={`rb-mode-btn${mode === m.id ? ' is-active' : ''}`}
              aria-pressed={mode === m.id}
              onClick={() => setMode(m.id)}
            >
              {m.label}
            </button>
          ))}
        </div>
        <div className="field rb-brush-field">
          <label htmlFor="rb-brush-radius">Brush size ({brushRadius}px)</label>
          <input id="rb-brush-radius" type="range" min={5} max={100} value={brushRadius}
            onChange={(e) => setBrushRadius(Number(e.target.value))} />
        </div>
      </div>

      <div className="spot-blur-stage">
        <img
          ref={imgRef}
          src={src}
          alt="Uploaded image to remove background from"
          className="spot-blur-image"
          onLoad={redraw}
          draggable={false}
        />
        <canvas
          ref={canvasRef}
          className="remove-bg-overlay"
          onPointerDown={handlePointerDown}
          onPointerMove={handlePointerMove}
          onPointerUp={stopPainting}
          onPointerLeave={stopPainting}
          onPointerCancel={stopPainting}
        />
      </div>

      <div className="rb-actions-row">
        <label className="rb-ai-toggle">
          <input type="checkbox" checked={useAi} onChange={(e) => setUseAi(e.target.checked)} />
          ใช้ AI ช่วย
        </label>
        {!useAi && !rect && (
          <span className="rb-ai-hint">ปิด AI ต้องลากกรอบอย่างน้อย 1 กรอบก่อน</span>
        )}
        <div className="rb-actions-buttons">
          <button type="button" className="btn btn-ghost" onClick={handleUndo} disabled={actions.length === 0}>
            ย้อนกลับ
          </button>
          <button type="button" className="btn btn-ghost" onClick={handleReset} disabled={actions.length === 0}>
            เริ่มใหม่
          </button>
        </div>
      </div>
    </div>
  )
}
