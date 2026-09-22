import { useLayoutEffect, useRef } from 'react'
import { Focus } from 'lucide-react'

export const FEATURES = [
  { id: 'spot-blur', icon: <Focus strokeWidth={1.75} />, title: 'Spot Blur', ready: true },
  { id: 'relight', icon: '✨', title: 'Relight', ready: false },
  { id: 'remove-object', icon: '✨', title: 'Remove Object', ready: false },
  { id: 'ai-enhance', icon: '✨', title: 'AI Enhance', ready: false },
]

const DURATION = 320

// The 4 tiles never unmount: `expanded` only swaps the container's layout
// (card row ↔ tab row) and the tiles FLIP-animate between their two positions.
export default function FeatureTabs({ expanded, activeId = 'spot-blur', onSelect, onBack }) {
  const tileRefs = useRef({})
  // "First" rects, captured right before the state change that re-lays-out the tiles.
  const firstRects = useRef(null)

  function captureFirst() {
    const rects = {}
    for (const f of FEATURES) {
      const el = tileRefs.current[f.id]
      if (el) rects[f.id] = el.getBoundingClientRect()
    }
    firstRects.current = rects
  }

  useLayoutEffect(() => {
    const first = firstRects.current
    firstRects.current = null
    if (!first) return
    if (window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) return

    const frames = []
    for (const f of FEATURES) {
      const el = tileRefs.current[f.id]
      const from = first[f.id]
      if (!el || !from) continue

      // Last: the tile is already in its new layout; drop any in-flight animation first.
      el.style.transition = 'none'
      el.style.transform = ''
      const to = el.getBoundingClientRect()
      if (!to.width || !to.height) continue

      // Invert: put it back where it visually was, no transition.
      const dx = from.left - to.left
      const dy = from.top - to.top
      const sx = from.width / to.width
      const sy = from.height / to.height
      el.style.transformOrigin = 'top left'
      el.style.transform = `translate(${dx}px, ${dy}px) scale(${sx}, ${sy})`

      // Play: next frame, release the transform with a transition.
      frames.push(requestAnimationFrame(() => {
        el.style.transition = `transform ${DURATION}ms ease-out`
        el.style.transform = ''
      }))
    }

    const cleanup = setTimeout(() => {
      for (const f of FEATURES) {
        const el = tileRefs.current[f.id]
        if (el) el.style.transition = ''
      }
    }, DURATION + 50)

    return () => {
      frames.forEach(cancelAnimationFrame)
      clearTimeout(cleanup)
    }
  }, [expanded])

  function handleSelect(id) {
    if (expanded) return
    captureFirst()
    onSelect(id)
  }

  function handleBack() {
    captureFirst()
    onBack()
  }

  return (
    <div className={`feature-tabs${expanded ? ' is-expanded' : ''}`}>
      <div className={expanded ? 'feature-tab-row' : 'feature-grid'}>
        {FEATURES.map((f) => {
          const isActive = expanded && f.id === activeId
          const className = [
            'feature-tile',
            f.ready ? 'is-ready' : 'is-inert',
            isActive ? 'is-active' : '',
          ].filter(Boolean).join(' ')

          return (
            <button
              key={f.id}
              ref={(el) => { tileRefs.current[f.id] = el }}
              type="button"
              className={className}
              disabled={!f.ready}
              aria-pressed={isActive}
              onClick={f.ready ? () => handleSelect(f.id) : undefined}
            >
              <span className="feature-tile-icon" aria-hidden="true">{f.icon}</span>
              <span className="feature-tile-title">{f.title}</span>
              {!f.ready && <span className="feature-tile-badge">Coming soon</span>}
            </button>
          )
        })}
      </div>

      {expanded && (
        <button type="button" className="feature-back" onClick={handleBack}>
          ← All features
        </button>
      )}
    </div>
  )
}
