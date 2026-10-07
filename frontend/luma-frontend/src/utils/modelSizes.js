// Recommended [width, height] pairs for the current model (Counterfeit-V3.0, SD 1.5).
// This list comes from Ice (confirmed sizes). When more models are added, or the
// backend adds a native_size field to /models, switch to that here — this is the
// only place that should change.
export const RECOMMENDED_SIZES = [
  [512, 1024],
  [1024, 512],
]

export function isRecommendedSize(width, height) {
  const w = Number(width)
  const h = Number(height)
  return RECOMMENDED_SIZES.some(([rw, rh]) => rw === w && rh === h)
}
