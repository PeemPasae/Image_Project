import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import MockModeBanner from '../MockModeBanner'
import NavIcon from '../NavIcon'
import { NAV_ITEMS } from './navItems'

function initialOf(email) {
  return (email || '?').trim().charAt(0).toUpperCase()
}

export default function SoftLayout() {
  const { logout, user } = useAuth()

  return (
    <div className="app-shell soft-shell">
      <aside className="soft-sidebar">
        <div className="soft-brand">
          <span className="soft-brand-mark" aria-hidden="true">
            <NavIcon name="sparkle" size={18} />
          </span>
          <span className="soft-brand-name">LUMA</span>
        </div>

        <nav aria-label="Main">
          <ul className="soft-nav">
            {NAV_ITEMS.map((item) => (
              <li key={item.to}>
                <NavLink
                  to={item.to}
                  end={item.end}
                  className={({ isActive }) => (isActive ? 'active' : '')}
                >
                  <NavIcon name={item.icon} size={18} />
                  <span>{item.label}</span>
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>

        <div className="soft-sidebar-footer">
          <button type="button" className="soft-logout" onClick={logout}>
            <NavIcon name="logout" size={18} />
            <span>Logout</span>
          </button>
          {user && (
            <div className="soft-user">
              <span className="soft-user-avatar" aria-hidden="true">{initialOf(user.email)}</span>
              <span className="soft-user-meta">
                <span className="soft-user-name">{user.email.split('@')[0]}</span>
                <span className="soft-user-email">{user.email}</span>
              </span>
            </div>
          )}
        </div>
      </aside>

      <main className="soft-main">
        <MockModeBanner />
        <Outlet />
      </main>
    </div>
  )
}
