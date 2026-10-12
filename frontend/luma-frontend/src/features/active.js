import { FEATURE_REGISTRY } from './registry'

// IDs shown in the 4-tile Features grid, in display order. Current value
// matches the 4 tools that have always been there.
export const ACTIVE_FEATURE_IDS = ['spot-blur', 'cartoonize', 'tilt-shift', 'hdr-enhancer']

/**
 * Resolves ACTIVE_FEATURE_IDS against FEATURE_REGISTRY: keeps registry order,
 * skips ids with no registry entry (warns) and entries marked available:false.
 * Never throws — the grid<->tabs morph in Features.jsx is tuned for exactly
 * 4 tiles, so a count other than 4 only warns.
 */
export function getActiveFeatures() {
  const features = []
  for (const id of ACTIVE_FEATURE_IDS) {
    const feature = FEATURE_REGISTRY[id]
    if (!feature) {
      console.warn(`getActiveFeatures: "${id}" is not in FEATURE_REGISTRY, skipping`)
      continue
    }
    if (feature.available === false) continue
    features.push(feature)
  }
  if (features.length !== 4) {
    console.warn(
      `getActiveFeatures: returning ${features.length} feature(s), but the Features page open/close animation is tuned for exactly 4 tiles`
    )
  }
  return features
}
