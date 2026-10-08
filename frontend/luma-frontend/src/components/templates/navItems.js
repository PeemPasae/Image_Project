// Single source of truth for sidebar navigation, shared by every template.
// Adding a route here makes it appear in all templates at once — templates
// should never keep their own copy of this list.

import { isAdmin } from '../../utils/roles'

export const NAV_ITEMS = [
  { to: '/', label: 'Home', icon: 'home', end: true },
  { to: '/generate', label: 'Generate', icon: 'sparkle' },
  { to: '/features', label: 'Features', icon: 'grid' },
  { to: '/history', label: 'History', icon: 'clock' },
  { to: '/profile', label: 'Profile', icon: 'user' },
  { to: '/setting', label: 'Settings', icon: 'settings' },
  { to: '/admin', label: 'Admin', icon: 'shield', adminOnly: true },
]

// UX only: hides admin entries from non-admins. The real check is on the backend.
export function visibleNavItems(user) {
  return NAV_ITEMS.filter((item) => !item.adminOnly || isAdmin(user))
}
