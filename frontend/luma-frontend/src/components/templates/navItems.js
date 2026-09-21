// Single source of truth for sidebar navigation, shared by every template.
// Adding a route here makes it appear in all templates at once — templates
// should never keep their own copy of this list.

export const NAV_ITEMS = [
  { to: '/', label: 'Home', icon: 'home', end: true },
  { to: '/generate', label: 'Generate', icon: 'sparkle' },
  { to: '/features', label: 'Features', icon: 'grid' },
  { to: '/history', label: 'History', icon: 'clock' },
  { to: '/profile', label: 'Profile', icon: 'user' },
  { to: '/setting', label: 'Settings', icon: 'settings' },
]
