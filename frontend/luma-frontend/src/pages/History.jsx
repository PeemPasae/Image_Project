import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { useToast } from '../context/ToastContext'

import AuthImage from '../components/AuthImage'
import SkeletonCard from '../components/SkeletonCard'

export default function History() {
  const navigate = useNavigate()
  const { showToast } = useToast()
  const [items, setItems] = useState([])
  const [pagination, setPagination] = useState({ page: 1, total_pages: 1 })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [deletingId, setDeletingId] = useState(null)

  function load(page) {
    setLoading(true)
    api.getHistory(page, 20)
      .then((data) => {
        setItems(data.history)
        setPagination(data.pagination)
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load(1) }, [])

  async function handleDelete(id) {
    if (!window.confirm('Delete this generation?')) return
    setDeletingId(id)
    try {
      await api.deleteGeneration(id)
      setItems((prev) => prev.filter((i) => i.id !== id))
      showToast('Generation deleted', 'success')
    } catch (err) {
      showToast(err.message, 'error')
    } finally {
      setDeletingId(null)
    }
  }

  function handleGenerateAgain(item, e) {
    e.preventDefault()
    navigate('/generate', {
      state: {
        prefill: {
          prompt: item.prompt,
          negative_prompt: item.negative_prompt || '',
          checkpoint: item.checkpoint,
          width: item.width,
          height: item.height,
          steps: item.steps || 20,
          cfg_scale: item.cfg_scale || 7,
          sampler: item.sampler || 'DPM++ 2M Karras',
          seed: -1,
        },
      },
    })
  }

  return (
    <div>
      <div className="page-header">
        <h1>Generation History</h1>
        <p>{pagination.total ?? items.length} total generations</p>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {loading ? (
        <div className="history-grid">
          {Array.from({ length: 8 }).map((_, i) => <SkeletonCard key={i} />)}
        </div>
      ) : items.length === 0 ? (
        <div className="empty-state card">
          No generations yet.
          <div><Link to="/generate" className="btn btn-primary">Create your first image</Link></div>
        </div>
      ) : (
        <>
          <div className="history-grid">
            {items.map((item) => (
              <div key={item.id} className="card history-card">
                <Link to={`/result/${item.id}`} className="history-thumb">
                  <AuthImage imageUrl={`/api/v1/images/${item.id}`} alt={item.prompt} />
                </Link>
                <div className="history-body">
                  <div className="history-prompt">{item.prompt}</div>
                  <div className="history-meta"><span>{item.checkpoint}</span><span>{item.width}×{item.height}</span></div>
                  <div className="history-actions">
                    <button className="btn btn-ghost" onClick={(e) => handleGenerateAgain(item, e)}>Again</button>
                    <button className="btn btn-danger" onClick={() => handleDelete(item.id)} disabled={deletingId === item.id}>
                      {deletingId === item.id ? <span className="spinner" /> : 'Delete'}
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {pagination.total_pages > 1 && (
            <div className="pagination">
              <button className="btn btn-ghost" disabled={pagination.page <= 1} onClick={() => load(pagination.page - 1)}>Prev</button>
              <span>Page {pagination.page} of {pagination.total_pages}</span>
              <button className="btn btn-ghost" disabled={pagination.page >= pagination.total_pages} onClick={() => load(pagination.page + 1)}>Next</button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
