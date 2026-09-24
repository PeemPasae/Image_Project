import { useLayoutEffect, useRef, useState } from 'react'
import { motion } from 'motion/react'
import { Focus, Palette, Aperture, Contrast } from 'lucide-react'

export const FEATURES = [
  { id: 'spot-blur', icon: <Focus strokeWidth={1.75} />, title: 'Spot Blur' },
  { id: 'cartoonize', icon: <Palette strokeWidth={1.75} />, title: 'Cartoonize' },
  { id: 'tilt-shift', icon: <Aperture strokeWidth={1.75} />, title: 'Tilt-Shift' },
  { id: 'hdr-enhancer', icon: <Contrast strokeWidth={1.75} />, title: 'HDR Enhancer' },
]

// Soft overshoot so the box stretches and settles a little, like liquid.
const MOVE = { type: 'spring', duration: 0.45, bounce: 0.2 }
const STAGGER = 0.03
const CONTENT_OUT = { duration: 0.1, ease: 'easeIn' }
const CONTENT_IN = { duration: 0.15, ease: 'easeOut' }
const BACK_OUT = { duration: 0.15, ease: 'easeIn' }
const BACK_IN = { duration: 0.2, ease: 'easeOut' }
const TAB_RADIUS = 12

// Reads the card radius (--ft-radius, differs per template) as a number so
// Motion can animate it between card and tab shapes.
function useCardRadius(ref, fallback = 16) {
  const [radius, setRadius] = useState(fallback)
  useLayoutEffect(() => {
    if (!ref.current) return
    const value = parseFloat(getComputedStyle(ref.current).getPropertyValue('--ft-radius'))
    if (Number.isFinite(value)) setRadius(value)
  }, [ref])
  return radius
}

function cornerRadii(top, bottom) {
  return {
    borderTopLeftRadius: top,
    borderTopRightRadius: top,
    borderBottomLeftRadius: bottom,
    borderBottomRightRadius: bottom,
  }
}

// Purely presentational: Features sequences the open/close/switch steps and
// drives these props. The tiles never unmount; Motion's `layout` animates
// each box between the card row and the tab bar (and, within the tab bar,
// between any tile becoming/un-becoming the active one) while its content is
// hidden — that per-tile `layout` interpolation is what makes the "joined"
// treatment read as sliding from tab to tab rather than jump-cutting.
//   layout         'grid' | 'tabs'
//   contentVisible icon/label shown (hidden while boxes morph)
//   joined         active tab drops its bottom border and merges with the panel
//   backVisible    "All features" button shown
export default function FeatureTabs({
  layout, contentVisible, joined, backVisible,
  activeId = null, onSelect, onBack, onTileSettled,
}) {
  const containerRef = useRef(null)
  const cardRadius = useCardRadius(containerRef)
  const tabs = layout === 'tabs'

  return (
    <div ref={containerRef} className={`feature-tabs${tabs ? ' is-expanded' : ''}`}>
      <div className={tabs ? 'feature-tab-row' : 'feature-grid'}>
        {FEATURES.map((f, i) => {
          const isActive = tabs && f.id === activeId
          const className = [
            'feature-tile',
            isActive ? 'is-active' : '',
            isActive && joined ? 'is-joined' : '',
          ].filter(Boolean).join(' ')

          // Staggered left→right into the tab bar, right→left back to the row.
          const order = tabs ? i : FEATURES.length - 1 - i

          return (
            <motion.button
              key={f.id}
              layout
              type="button"
              className={className}
              style={cornerRadii(cardRadius, cardRadius)}
              animate={tabs ? cornerRadii(TAB_RADIUS, 0) : cornerRadii(cardRadius, cardRadius)}
              transition={{ ...MOVE, delay: order * STAGGER }}
              aria-pressed={isActive}
              onClick={() => onSelect(f.id)}
              onLayoutAnimationComplete={() => onTileSettled?.(f.id)}
            >
              <motion.span
                className="feature-tile-content"
                initial={false}
                animate={{ opacity: contentVisible ? 1 : 0 }}
                transition={contentVisible ? CONTENT_IN : CONTENT_OUT}
              >
                <span className="feature-tile-icon" aria-hidden="true">{f.icon}</span>
                <span className="feature-tile-title">{f.title}</span>
              </motion.span>
            </motion.button>
          )
        })}
      </div>

      {tabs && (
        <motion.button
          type="button"
          className="feature-back"
          initial={{ opacity: 0 }}
          animate={{ opacity: backVisible ? 1 : 0 }}
          transition={backVisible ? BACK_IN : BACK_OUT}
          style={{ pointerEvents: backVisible ? 'auto' : 'none' }}
          onClick={onBack}
          disabled={!backVisible}
        >
          ← All features
        </motion.button>
      )}
    </div>
  )
}
