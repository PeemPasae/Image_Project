// Layout templates — each entry is a shell variant the user can switch between.
// This is deliberately separate from src/themes/presets.js: themes control COLOR,
// templates control LAYOUT. The two compose freely (any theme x any template).

export const TEMPLATES = [
  {
    id: 'classic',
    label: 'Classic',
    description: 'Compact sidebar, dense grid. The original LUMA layout.',
  },
  {
    id: 'soft',
    label: 'Soft',
    description: 'Roomier spacing, larger imagery, calmer type. Easier on the eyes.',
  },
]
 
export const DEFAULT_TEMPLATE_ID = 'soft'

export function getTemplateById(id) {
  return (
    TEMPLATES.find((t) => t.id === id) ||
    TEMPLATES.find((t) => t.id === DEFAULT_TEMPLATE_ID)
  )
}
