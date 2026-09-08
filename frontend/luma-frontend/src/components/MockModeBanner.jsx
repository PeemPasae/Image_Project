import { MOCK_MODE } from '../api/client'

export default function MockModeBanner() {
  if (!MOCK_MODE) return null
  return (
    <div style={{
      background: 'rgba(251,191,36,0.12)',
      border: '1px solid rgba(251,191,36,0.35)',
      color: 'var(--warning)',
      fontSize: 12.5,
      padding: '8px 14px',
      borderRadius: 8,
      marginBottom: 16,
      textAlign: 'center',
    }}>
      Dev Preview Mode — showing mock data, no Backend connected
    </div>
  )
}
