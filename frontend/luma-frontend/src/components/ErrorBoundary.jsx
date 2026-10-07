import { Component } from 'react'

export default class ErrorBoundary extends Component {
  state = { hasError: false }

  static getDerivedStateFromError() {
    return { hasError: true }
  }

  componentDidCatch(error, info) {
    console.error('Unhandled UI error:', error, info?.componentStack)
  }

  render() {
    if (!this.state.hasError) return this.props.children
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20, background: 'var(--bg)', color: 'var(--text)' }}>
        <div className="card" role="alert" style={{ maxWidth: 420, textAlign: 'center' }}>
          <p style={{ fontWeight: 700, marginBottom: 16 }}>เกิดข้อผิดพลาดบางอย่าง กรุณาลองใหม่อีกครั้ง</p>
          <button type="button" className="btn btn-primary" onClick={() => window.location.reload()}>โหลดหน้าใหม่</button>
        </div>
      </div>
    )
  }
}
