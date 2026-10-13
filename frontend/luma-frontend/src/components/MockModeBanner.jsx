import { MOCK_MODE } from '../api/client'

export default function MockModeBanner() {
  if (!MOCK_MODE) return null
  return (
    <div className="alert alert-warning" role="status">
      <span className="alert-dot" aria-hidden="true" />
      <span>
        <strong>Dev Preview Mode</strong> — showing mock data, no backend connected
      </span>
    </div>
  )
}