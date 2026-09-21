import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import MockModeBanner from '../MockModeBanner'
import { NAV_ITEMS } from './navItems'

export default function ClassicLayout() {
  const { logout } = useAuth()

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">L</div>
          <div className="brand-name">LUMA</div>
        </div>
        <ul className="nav-list">
          {NAV_ITEMS.map((item) => (
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
