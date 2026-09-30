// Single source of truth for every image tool in the app (used by both
// FeatureTabs.jsx and Features.jsx — see src/features/active.js for which
// ones are actually shown and in what order).
//
// To add a new tool:
//   1. Add an entry below (id, title, icon, component, subtitle, available).
//   2. Write the tool component (follow the pattern in src/components/features/*.jsx).
//   3. Add a client method for it in src/api/client.js (api.processXxx).
//   4. Add its id to ACTIVE_FEATURE_IDS in src/features/active.js so it renders.
import { createElement } from 'react'
import { Focus, Palette, Aperture, Contrast, Hand, Eraser } from 'lucide-react'
import SpotBlurTool from '../components/features/SpotBlurTool'
import CartoonizeTool from '../components/features/CartoonizeTool'
import TiltShiftTool from '../components/features/TiltShiftTool'
import HdrEnhancerTool from '../components/features/HdrEnhancerTool'
import HandGestureTool from '../components/features/HandGestureTool'
import RemoveBackgroundTool from '../components/features/RemoveBackgroundTool'

export const FEATURE_REGISTRY = {
  'spot-blur': {
    id: 'spot-blur',
    title: 'Spot Blur',
    icon: createElement(Focus, { strokeWidth: 1.75 }),
    subtitle: 'Pick a spot, blur it.',
    component: SpotBlurTool,
    available: true,
  },
  cartoonize: {
    id: 'cartoonize',
    title: 'Cartoonize',
    icon: createElement(Palette, { strokeWidth: 1.75 }),
    subtitle: 'Turn your photo into a cartoon/anime style.',
    component: CartoonizeTool,
    available: true,
  },
  'tilt-shift': {
    id: 'tilt-shift',
    title: 'Tilt-Shift',
    icon: createElement(Aperture, { strokeWidth: 1.75 }),
    subtitle: 'Simulate a tilt-shift, miniature-model look.',
    component: TiltShiftTool,
    available: true,
  },
  'hdr-enhancer': {
    id: 'hdr-enhancer',
    title: 'HDR Enhancer',
    icon: createElement(Contrast, { strokeWidth: 1.75 }),
    subtitle: 'Boost detail and contrast, HDR-style.',
    component: HdrEnhancerTool,
    available: true,
  },
  'hand-gesture': {
    id: 'hand-gesture',
    title: 'Hand Gesture',
    icon: createElement(Hand, { strokeWidth: 1.75 }),
    subtitle: 'Recognize a hand gesture in a photo.',
    component: HandGestureTool,
    available: true,
  },
  'remove-background': {
    id: 'remove-background',
    title: 'Remove Background',
    icon: createElement(Eraser, { strokeWidth: 1.75 }),
    subtitle: 'Cut the background out of a photo.',
    component: RemoveBackgroundTool,
    available: true,
  },
}
