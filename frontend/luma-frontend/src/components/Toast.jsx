import { useToast } from '../context/ToastContext'

const ICONS = { success: '✓', error: '✕' }

export default function ToastContainer() {
  const { toasts, removeToast } = useToast()

  if (toasts.length === 0) return null

  return (
    <div className="toast-stack">
      {toasts.map((t) => (
        <div key={t.id} className={`toast toast-${t.type}`} onClick={() => removeToast(t.id)}>
          <span className="toast-icon">{ICONS[t.type] || '!'}</span>
          <span>{t.message}</span>
        </div>
      ))}
    </div>
  )
}