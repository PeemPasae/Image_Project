import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'
import AuthImage from '../components/AuthImage'
import SkeletonCard from '../components/SkeletonCard'

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
        <h1>Welcome{user ? `, ${user.email}` : ''}</h1>
        <p>Ready to generate something new?</p>
      </div>

      <div className="card" style={{ marginBottom: 28, display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <div style={{ fontWeight: 700, marginBottom: 4 }}>New Generation</div>
          <div style={{ fontSize: 12.5, color: 'var(--text-dim)' }}>Write a prompt and let Stable Diffusion do the rest.</div>
        </div>
        <Link to="/generate" className="btn btn-primary">Generate an image</Link>
      </div>

      <div className="card" style={{ marginBottom: 28, display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <div style={{ fontWeight: 700, marginBottom: 4 }}>✨ Features</div>
          <div style={{ fontSize: 12.5, color: 'var(--text-dim)' }}>New tools are coming — take a look.</div>
        </div>
        <Link to="/features" className="btn btn-primary">Explore Features</Link>
      </div>

      <div className="page-header"><h1 style={{ fontSize: 16 }}>Recent Generations</h1></div>
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
            <Link key={item.id} to={`/result/${item.id}`} className="card history-card">
              <div className="history-thumb">
                <AuthImage imageUrl={`/api/v1/images/${item.id}`} alt={item.prompt} />
              </div>
              <div className="history-body">
                <div className="history-prompt">{item.prompt}</div>
                <div className="history-meta"><span>{item.checkpoint}</span><span>{item.width}×{item.height}</span></div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}