import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import MockModeBanner from './MockModeBanner'

const NAV = [
  { to: '/', label: 'Home', end: true },
  { to: '/generate', label: 'Generate' },
  { to: '/features', label: 'Features' },
  { to: '/history', label: 'History' },
  { to: '/profile', label: 'Profile' },
  { to: '/setting', label: 'Setting' },
]

export default function Layout() {
  const { logout } = useAuth()

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">L</div>
          <div className="brand-name">LUMA</div>
        </div>
        <ul className="nav-list">
          {NAV.map((item) => (
            <li key={item.to}>
              <NavLink to={item.to} end={item.end} className={({ isActive }) => (isActive ? 'active' : '')}>
                {item.label}
              </NavLink>
            </li>
          ))}
        </ul>
        <div className="sidebar-footer">
          <button className="btn btn-ghost logout-btn" onClick={logout}>Logout</button>
        </div>
      </aside>
      <main className="main-content">
        <MockModeBanner />
        <Outlet />
      </main>
    </div>
  )
}
