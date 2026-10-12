import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { isAdmin } from '../utils/roles'

const FORBIDDEN_MESSAGE = 'คุณไม่มีสิทธิ์เข้าถึงหน้านี้'

function formatDate(iso) {
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? '-' : d.toLocaleDateString('th-TH', { year: 'numeric', month: 'short', day: 'numeric' })
}

// SECURITY NOTE: hiding the Admin menu and checking the role here are UX only —
// anyone can edit localStorage or call the API directly. Real protection lives in
// the backend, which must answer 403 (FORBIDDEN) to non-admin callers.
export default function Admin() {
  const { user } = useAuth()
  const { showToast } = useToast()
  const allowed = isAdmin(user)
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(allowed)
  const [error, setError] = useState('')
  const [forbidden, setForbidden] = useState(false)
  const [target, setTarget] = useState(null)
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    if (!allowed) return
    api.getAdminUsers()
      .then((data) => setUsers(data.users))
      .catch((err) => (err.code === 'FORBIDDEN' ? setForbidden(true) : setError(err.message)))
      .finally(() => setLoading(false))
  }, [allowed])

  useEffect(() => {
    if (!target) return undefined
    function onKey(e) { if (e.key === 'Escape' && !deleting) setTarget(null) }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [target, deleting])

  async function confirmDelete() {
    setDeleting(true)
    try {
      await api.deleteAdminUser(target.id)
      setUsers((list) => list.filter((u) => u.id !== target.id))
      showToast(`ลบผู้ใช้ ${target.email} เรียบร้อยแล้ว`, 'success')
    } catch (err) {
      if (err.code === 'FORBIDDEN') setForbidden(true)
      else showToast(err.message)
    } finally {
      setDeleting(false)
      setTarget(null)
    }
  }

  if (!allowed || forbidden) {
    return (
      <div className="empty-state" role="alert">
        <h2 style={{ marginBottom: 8 }}>{FORBIDDEN_MESSAGE}</h2>
        <p>กรุณาติดต่อผู้ดูแลระบบหากคุณคิดว่านี่เป็นความผิดพลาด</p>
      </div>
    )
  }

  return (
    <div>
      <div className="page-header">
        <h1>จัดการผู้ใช้</h1>
        <p>ลบบัญชีผู้ใช้ที่ไม่ต้องการออกจากระบบ</p>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {loading ? (
        <div className="empty-state"><span className="spinner" /> กำลังโหลด…</div>
      ) : !error && users.length === 0 ? (
        <div className="empty-state">ยังไม่มีผู้ใช้ในระบบ</div>
      ) : users.length > 0 && (
        <div className="card admin-table-wrap">
          <table className="admin-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>อีเมล</th>
                <th>วันที่สมัคร</th>
                <th className="num">จำนวนภาพที่สร้าง</th>
                <th><span className="sr-only">การดำเนินการ</span></th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => {
                const isSelf = u.id === user.id
                return (
                  <tr key={u.id}>
                    <td className="mono">{u.id}</td>
                    <td>{u.email}</td>
                    <td>{formatDate(u.created_at)}</td>
                    <td className="num">{u.generation_count}</td>
                    <td className="actions">
                      <button
                        type="button"
                        className="btn btn-danger"
                        disabled={isSelf}
                        title={isSelf ? 'ไม่สามารถลบบัญชีของตัวเองได้' : undefined}
                        onClick={() => setTarget(u)}
                      >
                        ลบ
                      </button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      {target && (
        <div className="modal-backdrop" onClick={() => !deleting && setTarget(null)}>
          <div className="modal card" role="dialog" aria-modal="true" aria-labelledby="del-title" onClick={(e) => e.stopPropagation()}>
            <h2 id="del-title" style={{ fontSize: 18, marginBottom: 10 }}>ยืนยันการลบผู้ใช้</h2>
            <p style={{ color: 'var(--text-dim)', fontSize: 14 }}>
              คุณต้องการลบผู้ใช้ <strong style={{ color: 'var(--text)' }}>{target.email}</strong> ใช่หรือไม่ การดำเนินการนี้ไม่สามารถย้อนกลับได้
            </p>
            <div className="action-row" style={{ justifyContent: 'flex-end' }}>
              <button type="button" className="btn btn-ghost" onClick={() => setTarget(null)} disabled={deleting}>ยกเลิก</button>
              <button type="button" className="btn btn-danger" onClick={confirmDelete} disabled={deleting}>
                {deleting ? <span className="spinner" /> : 'ลบผู้ใช้'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
