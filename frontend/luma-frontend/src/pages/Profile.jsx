import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'

export default function Profile() {
  const { logout } = useAuth()
  const [profile, setProfile] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api.getProfile().then(setProfile).catch((err) => setError(err.message))
  }, [])

  return (
    <div>
      <div className="page-header">
        <h1>Profile</h1>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {profile && (
        <div className="card" style={{ maxWidth: 420 }}>
          <div className="stat-row">
            <div className="stat-box">
              <div className="num">{profile.generation_count}</div>
              <div className="label">Generations</div>
            </div>
          </div>
          <div className="param-list">
            <div className="param-row"><span className="k">Email</span><span className="v">{profile.email}</span></div>
            <div className="param-row"><span className="k">User ID</span><span className="v">{profile.id}</span></div>
            <div className="param-row"><span className="k">Created</span><span className="v">{profile.created_at}</span></div>
          </div>
          <div className="action-row">
            <button className="btn btn-ghost" disabled title="Coming soon">Change Password</button>
            <button className="btn btn-danger" onClick={logout}>Logout</button>
          </div>
        </div>
      )}
    </div>
  )
}
