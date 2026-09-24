import { useEffect, useRef, useState } from 'react'
import { flushSync } from 'react-dom'
import { MotionConfig, motion, useReducedMotion } from 'motion/react'
import FeatureTabs, { FEATURES } from '../components/features/FeatureTabs'
import SpotBlurTool from '../components/features/SpotBlurTool'
import CartoonizeTool from '../components/features/CartoonizeTool'
import TiltShiftTool from '../components/features/TiltShiftTool'
import HdrEnhancerTool from '../components/features/HdrEnhancerTool'
import '../styles/features.css'

// Page-level concern (subtitle text, which component renders in the panel)
// keyed by tile id — FeatureTabs itself stays presentation-only.
const TOOL_META = {
  'spot-blur': { subtitle: 'Pick a spot, blur it.', Component: SpotBlurTool },
  cartoonize: { subtitle: 'Turn your photo into a cartoon/anime style.', Component: CartoonizeTool },
  'tilt-shift': { subtitle: 'Simulate a tilt-shift, miniature-model look.', Component: TiltShiftTool },
  'hdr-enhancer': { subtitle: 'Boost detail and contrast, HDR-style.', Component: HdrEnhancerTool },
}

// ---- Timings (ms) ----
const CONTENT_FADE_OUT = 100
const PANEL_CONTENT_FADE_IN = 200 // opening: panel content + back button fade in
const PANEL_CONTENT_FADE_OUT = 150 // closing: panel content + back button fade out
const SWITCH_FADE_OUT = 120 // fading out the old tool's content before a same-open tab switch
const SWITCH_FADE_IN = 150 // fading in the new tool's content after
const SETTLE_FALLBACK = 1000 // if a tile's onLayoutAnimationComplete never fires

// Panel "bouncy pour" (open) / pour-back (close). Rectangle the whole way —
// no % radii, no round/oval shape at any frame. Height and width run as two
// separately-timed WAAPI tracks (not one shared keyframe list) so each can
// overshoot and settle on its own; width is staggered to start after height
// leads in (open) or finish after width leads out (close), so the two overlap
// rather than running strictly one-after-the-other.
const PANEL_RADIUS = 12 // matches .feature-panel's resting border-radius
const RADIUS_OPEN = `0 0 ${PANEL_RADIUS}px ${PANEL_RADIUS}px` // no top-right corner: width == tab width
const RADIUS_FULL = `0 ${PANEL_RADIUS}px ${PANEL_RADIUS}px ${PANEL_RADIUS}px` // top-left stays 0, flush under the tab

const OPEN_HEIGHT = { duration: 520, delay: 0, easing: 'cubic-bezier(.34,1.56,.64,1)' } // ~10% overshoot
const OPEN_WIDTH = { duration: 560, delay: 80, easing: 'cubic-bezier(.32,1.35,.58,1)' } // ~6% overshoot, starts once height is under way
const OPEN_RADIUS = { duration: 560, delay: 80, easing: 'ease-out' }

const CLOSE_WIDTH = { duration: 320, delay: 0, easing: 'cubic-bezier(.36,0,.66,-.3)' } // slight outward overshoot before it shrinks
const CLOSE_HEIGHT = { duration: 350, delay: 100, easing: 'cubic-bezier(.36,0,.66,-.2)' }
const CLOSE_RADIUS = { duration: 320, delay: 0, easing: 'ease-in' }
const CLOSE_TOTAL = Math.max(CLOSE_WIDTH.duration, CLOSE_HEIGHT.delay + CLOSE_HEIGHT.duration)

function animateProp(el, prop, from, to, { duration, delay, easing }) {
  if (typeof el.animate !== 'function') return null
  // fill: 'both' holds `from` during `delay` so a staggered track doesn't
  // snap to its CSS default before its turn starts.
  return el.animate([{ [prop]: from }, { [prop]: to }], { duration, delay, easing, fill: 'both' })
}

function inflatePanel(el, x0, w0, W, H) {
  return [
    animateProp(el, 'height', '0px', `${H}px`, OPEN_HEIGHT),
    animateProp(el, 'width', `${w0}px`, `${W}px`, OPEN_WIDTH),
    animateProp(el, 'left', `${x0}px`, '0px', OPEN_WIDTH),
    animateProp(el, 'borderRadius', RADIUS_OPEN, RADIUS_FULL, OPEN_RADIUS),
  ].filter(Boolean)
}

function deflatePanel(el, x0, w0, W, H) {
  return [
    animateProp(el, 'width', `${W}px`, `${w0}px`, CLOSE_WIDTH),
    animateProp(el, 'left', '0px', `${x0}px`, CLOSE_WIDTH),
    animateProp(el, 'height', `${H}px`, '0px', CLOSE_HEIGHT),
    animateProp(el, 'borderRadius', RADIUS_FULL, RADIUS_OPEN, CLOSE_RADIUS),
  ].filter(Boolean)
}

const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

const INITIAL = {
  layout: 'grid',       // 'grid' | 'tabs'
  content: true,        // tile icons/labels visible
  joined: false,        // active tab merged with the panel
  panel: false,         // panel mounted
  panelContent: false,  // active tool visible inside the panel
  back: false,          // "All features" visible
  activeId: null,        // which tile is open ('spot-blur', 'cartoonize', …)
  switching: false,      // mid same-open tool switch (picks the fade durations below)
}

// Open:   content out → tiles morph to tabs → tab joins, panel pours out of
//         it → panel content + back button fade in.
// Close:  panel content + back out → panel pours back into the tab → tab
//         detaches, content out, tiles morph back → content in.
// Switch: (panel already open, a different live tab clicked) old content
//         fades out → activeId flips, so the "joined" tall-tab treatment
//         slides from the old tab to the new one and the panel glides to the
//         new tool's height (same `.is-settled` transition as an image
//         upload) → new content fades in. No morph/bouncy-pour replay.
export default function Features() {
  const reduceMotion = useReducedMotion()
  const [ui, setUi] = useState(INITIAL)
  const stageRef = useRef(null)
  const panelRef = useRef(null)
  const bodyRef = useRef(null)
  const busy = useRef(false)
  const runId = useRef(0)
  const anim = useRef(null)
  const settleWaiters = useRef(new Set())

  useEffect(() => () => {
    runId.current++ // abandon any running sequence
    anim.current?.forEach((a) => a.cancel())
  }, [])

  // Once open() hands the panel back to `height: auto` (`.is-settled`), later
  // content-driven height changes — e.g. an image upload changing the tool's
  // natural height — get a short WAAPI transition instead of an instant jump.
  // A plain CSS `transition: height` can't do this: it doesn't animate to/from
  // `auto`, which is what the panel rests at.
  useEffect(() => {
    const panel = panelRef.current
    const body = bodyRef.current
    if (!ui.panel || !panel || !body) return

    let settledHeight = null
    let resizeAnim = null

    const ro = new ResizeObserver(() => {
      if (!panel.classList.contains('is-settled')) return // mid open/close sequence
      const next = panel.getBoundingClientRect().height
      if (settledHeight == null) { settledHeight = next; return }
      if (Math.abs(next - settledHeight) < 1) return
      const from = settledHeight
      settledHeight = next
      resizeAnim?.cancel()
      resizeAnim = panel.animate(
        [{ height: `${from}px` }, { height: `${next}px` }],
        { duration: 250, easing: 'ease', fill: 'forwards' }
      )
      resizeAnim.finished.then(() => {
        resizeAnim?.cancel()
        resizeAnim = null
        panel.style.height = ''
      }).catch(() => {})
    })
    ro.observe(body)

    return () => {
      ro.disconnect()
      resizeAnim?.cancel()
    }
  }, [ui.panel])

  function update(patch, sync = false) {
    const apply = () => setUi((u) => ({ ...u, ...patch }))
    if (sync) flushSync(apply)
    else apply()
  }

  // Resolves once every tile has finished its layout animation.
  function tilesSettled() {
    return new Promise((resolve) => {
      const pending = new Set(FEATURES.map((f) => f.id))
      const onId = (id) => {
        pending.delete(id)
        if (pending.size === 0) done()
      }
      const done = () => {
        clearTimeout(timer)
        settleWaiters.current.delete(onId)
        resolve()
      }
      const timer = setTimeout(done, SETTLE_FALLBACK)
      settleWaiters.current.add(onId)
    })
  }

  // Resolves once one specific tile finishes its own layout animation — lets
  // the panel start pouring as soon as its anchor (the active tab) is ready,
  // instead of waiting on the other, still-staggering tiles to catch up too.
  function tileSettled(id) {
    return new Promise((resolve) => {
      const onId = (settledId) => {
        if (settledId === id) done()
      }
      const done = () => {
        clearTimeout(timer)
        settleWaiters.current.delete(onId)
        resolve()
      }
      const timer = setTimeout(done, SETTLE_FALLBACK)
      settleWaiters.current.add(onId)
    })
  }

  function activeTabWidth() {
    return stageRef.current?.querySelector('.feature-tile.is-active')?.offsetWidth ?? 0
  }

  // x offset of the active tab relative to the stage — where the panel's
  // narrow (tab-width) state should sit, since it's the currently active
  // tile that's flush against it, not necessarily tile 0.
  function activeTabOffset() {
    const stage = stageRef.current
    const tab = stage?.querySelector('.feature-tile.is-active')
    if (!stage || !tab) return 0
    return tab.getBoundingClientRect().left - stage.getBoundingClientRect().left
  }

  async function open(id) {
    if (busy.current || ui.layout !== 'grid') return
    busy.current = true
    const run = ++runId.current
    const alive = () => run === runId.current

    if (reduceMotion) {
      update({ activeId: id, layout: 'tabs', joined: true, panel: true }, true)
      update({ panelContent: true, back: true })
      busy.current = false
      return
    }

    update({ content: false })
    await wait(CONTENT_FADE_OUT)
    if (!alive()) return

    // Two separate gates from here: the panel only needs its own anchor (the
    // active tab) settled, while the tab labels wait on the whole group —
    // decoupled so the panel doesn't sit idle for the ~150ms tail of the
    // other, still-staggering tiles finishing their own spring.
    const allSettled = tilesSettled()
    const activeSettled = tileSettled(id)
    update({ activeId: id, layout: 'tabs' }, true)
    allSettled.then(() => { if (alive()) update({ content: true }) })

    await activeSettled
    if (!alive()) return

    update({ joined: true, panel: true }, true)
    const panel = panelRef.current
    const body = bodyRef.current
    if (panel && body) {
      // Lay the tool out at its final width from the start; the panel clips it.
      const W = stageRef.current.clientWidth
      body.style.width = `${W - 2}px` // inside the panel's 1px side borders
      const H = body.offsetHeight + 2 // + panel's top/bottom border
      anim.current = inflatePanel(panel, activeTabOffset(), activeTabWidth(), W, H)
      await Promise.all(anim.current.map((a) => a.finished.catch(() => {})))
      if (!alive()) return
      // Release the fixed size so the panel follows its content (image upload).
      anim.current.forEach((a) => a.cancel())
      anim.current = null
      body.style.width = ''
      // From here the panel's height tracks its content via CSS, not JS.
      panel.classList.add('is-settled')
    }

    await allSettled
    if (!alive()) return

    update({ panelContent: true, back: true })
    busy.current = false
  }

  async function close() {
    if (busy.current || ui.layout !== 'tabs') return
    busy.current = true
    const run = ++runId.current
    const alive = () => run === runId.current

    update({ panelContent: false, back: false })
    await wait(PANEL_CONTENT_FADE_OUT)
    if (!alive()) return

    if (reduceMotion) {
      update({ layout: 'grid', joined: false, panel: false })
      busy.current = false
      return
    }

    const panel = panelRef.current
    const body = bodyRef.current
    if (panel && body) {
      // Drop the CSS-driven settle transition — the JS tracks below take over.
      panel.classList.remove('is-settled')
      const W = panel.offsetWidth
      const H = panel.offsetHeight
      body.style.width = `${panel.clientWidth}px`
      anim.current = deflatePanel(panel, activeTabOffset(), activeTabWidth(), W, H)
      // Tab content starts fading just before the pour-back lands, so the tiles
      // can move the moment it does — no idle gap.
      const fade = setTimeout(() => update({ content: false }), CLOSE_TOTAL - CONTENT_FADE_OUT)
      await Promise.all(anim.current.map((a) => a.finished.catch(() => {})))
      clearTimeout(fade)
      if (!alive()) return
      anim.current = null
    }

    const settled = tilesSettled()
    update({ content: false, joined: false, panel: false, layout: 'grid' }, true)
    await settled
    if (!alive()) return

    update({ content: true })
    busy.current = false
  }

  // Panel already open, a different live tab clicked. No morph/bouncy-pour —
  // just fade the content, swap which tab is joined + which tool renders, and
  // let the panel's existing `.is-settled` resize transition (see the
  // ResizeObserver effect above) glide it to the new tool's height.
  async function switchTool(id) {
    if (busy.current || ui.layout !== 'tabs' || id === ui.activeId) return
    busy.current = true
    const run = ++runId.current
    const alive = () => run === runId.current

    if (reduceMotion) {
      update({ activeId: id })
      busy.current = false
      return
    }

    update({ switching: true, panelContent: false })
    await wait(SWITCH_FADE_OUT)
    if (!alive()) return

    update({ activeId: id, panelContent: true }, true)
    await wait(SWITCH_FADE_IN)
    if (!alive()) return

    update({ switching: false })
    busy.current = false
  }

  const ActiveTool = TOOL_META[ui.activeId]?.Component

  return (
    <MotionConfig reducedMotion="user">
      <div>
        <div className="page-header">
          <h1>Features</h1>
          <p>{ui.layout === 'grid' ? 'Image tools for your generations — more on the way.' : TOOL_META[ui.activeId]?.subtitle}</p>
        </div>

        <div className="feature-stage" ref={stageRef}>
          <FeatureTabs
            layout={ui.layout}
            contentVisible={ui.content}
            joined={ui.joined}
            backVisible={ui.back}
            activeId={ui.activeId}
            onSelect={(id) => {
              if (ui.layout === 'grid') open(id)
              else if (id !== ui.activeId) switchTool(id)
            }}
            onBack={close}
            onTileSettled={(id) => settleWaiters.current.forEach((fn) => fn(id))}
          />

          {ui.panel && (
            <div className="feature-panel" ref={panelRef}>
              <motion.div
                ref={bodyRef}
                className="feature-panel-body"
                initial={{ opacity: 0 }}
                animate={{ opacity: ui.panelContent ? 1 : 0 }}
                transition={{
                  duration: (ui.panelContent
                    ? (ui.switching ? SWITCH_FADE_IN : PANEL_CONTENT_FADE_IN)
                    : (ui.switching ? SWITCH_FADE_OUT : PANEL_CONTENT_FADE_OUT)) / 1000,
                  ease: 'easeOut',
                }}
              >
                {ActiveTool && <ActiveTool />}
              </motion.div>
            </div>
          )}
        </div>
      </div>
    </MotionConfig>
  )
}
