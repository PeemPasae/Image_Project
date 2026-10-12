import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'
import AuthImage from '../components/AuthImage'
import SkeletonCard from '../components/SkeletonCard'
import NavIcon from '../components/NavIcon'

// papangkorn.choowong@gmail.com -> "Papangkorn"
// ถ้าอยากโชว์อีเมลเต็มเหมือนเดิม เปลี่ยนบรรทัด <h1> เป็น {user.email} ได้เลย
function displayName(user) {
  if (!user?.email) return 'there'
  const first = user.email.split('@')[0].split(/[._\-+]/)[0]
  return first.charAt(0).toUpperCase() + first.slice(1)
}

export default function Home() {
  const { user } = useAuth()
  const [recent, setRecent] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.getHistory(1, 4)
      .then((data) => setRecent(data.history))
      .catch(() => setRecent([]))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div>
      <div className="page-header">
        <h1>Welcome{user ? `, ${displayName(user)}` : ''}</h1>
        <p>Ready to generate something new?</p>
      </div>

      {/* กล่องที่ 1 — Generate */}
      <div className="card action-card">
        <span className="action-card-icon" aria-hidden="true">
          <NavIcon name="sparkle" size={20} />
        </span>
        <div className="action-card-text">
          <div className="action-card-title">New Generation</div>
          <div className="action-card-desc">Write a prompt and let Stable Diffusion do the rest.</div>
        </div>
        <Link to="/generate" className="btn btn-primary">Generate an image</Link>
      </div>

      {/* กล่องที่ 2 — Features */}
      <div className="card action-card">
        <span className="action-card-icon action-card-icon-alt" aria-hidden="true">
          <NavIcon name="grid" size={20} />
        </span>
        <div className="action-card-text">
          <div className="action-card-title">Features</div>
          <div className="action-card-desc">New tools are coming — take a look.</div>
        </div>
        <Link to="/features" className="btn btn-secondary">Explore Features</Link>
      </div>

      <div className="section-head">
        <h2>Recent Generations</h2>
        <Link to="/history" className="section-link">View all →</Link>
      </div>

      {loading ? (
        <div className="history-grid">
          {Array.from({ length: 4 }).map((_, i) => <SkeletonCard key={i} />)}
        </div>
      ) : recent.length === 0 ? (
        <div className="empty-state card">
          No generations yet.
          <div><Link to="/generate" className="btn btn-primary">Create your first image</Link></div>
        </div>
      ) : (
        <div className="history-grid">
          {recent.map((item) => (
            <Link key={item.id} to={`/result/${item.id}`} className="card history-card card-hoverable">
              <div className="history-thumb">
                <AuthImage imageUrl={`/api/v1/images/${item.id}`} alt={item.prompt} />
              </div>
              <div className="history-body">
                <div className="history-prompt">{item.prompt}</div>
                <div className="history-meta">
                  <span>{item.checkpoint}</span>
                  <span>{item.width} × {item.height}</span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}