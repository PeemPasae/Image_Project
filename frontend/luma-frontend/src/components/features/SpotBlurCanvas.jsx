import { useCallback, useEffect, useRef } from 'react'

// Image + absolutely-positioned <canvas> overlay the user paints circles on.
// `circles` is [{x, y, r}] in the ORIGINAL image's pixel space — the image is
// usually displayed smaller than its natural size, so every pointer position
// and the brush radius are scaled by natural/displayed before being stored.
export default function SpotBlurCanvas({ src, circles, onChange, brushRadius }) {
  const imgRef = useRef(null)
  const canvasRef = useRef(null)
  const painting = useRef(false)
  const lastCircle = useRef(null)
  // Latest circles for pointer handlers, without re-binding them on every stroke.
  const circlesRef = useRef(circles)
  circlesRef.current = circles

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

    // Circles are drawn opaque in the theme accent; the canvas itself carries
    // the ~35% opacity (see features.css) so overlaps don't stack darker.
    ctx.fillStyle = getComputedStyle(canvas).color
    for (const c of circlesRef.current) {
      ctx.beginPath()
      ctx.arc(c.x / scale.x, c.y / scale.y, c.r / scale.x, 0, Math.PI * 2)
      ctx.fill()
    }
  }, [])

  useEffect(() => { redraw() }, [circles, redraw])

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
    const rect = canvasRef.current.getBoundingClientRect()
    return {
      x: (e.clientX - rect.left) * scale.x,
      y: (e.clientY - rect.top) * scale.y,
      r: brushRadius * scale.x,
    }
  }

  function addCircle(c) {
    lastCircle.current = c
    // Update the ref immediately so several moves before the next render all land.
    const next = [...circlesRef.current, c]
    circlesRef.current = next
    onChange(next)
  }

  function handlePointerDown(e) {
    if (e.button !== undefined && e.button !== 0) return
    const c = toNatural(e)
    if (!c) return
    e.preventDefault()
    painting.current = true
    addCircle(c)
  }

  function handlePointerMove(e) {
    if (!painting.current) return
    const c = toNatural(e)
    const last = lastCircle.current
    if (!c || !last) return
    // Only add a circle once the cursor has travelled ~r/3 — continuous stroke
    // without flooding the array with near-duplicates.
    if (Math.hypot(c.x - last.x, c.y - last.y) > c.r / 3) addCircle(c)
  }

  function stopPainting() {
    painting.current = false
    lastCircle.current = null
  }

  return (
    <div className="spot-blur-stage">
      <img
        ref={imgRef}
        src={src}
        alt="Uploaded image to blur"
        className="spot-blur-image"
        onLoad={redraw}
        draggable={false}
      />
      <canvas
        ref={canvasRef}
        className="spot-blur-overlay"
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={stopPainting}
        onPointerLeave={stopPainting}
        onPointerCancel={stopPainting}
      />
    </div>
  )
}
