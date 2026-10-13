import { describe, it, expect, vi, afterEach } from 'vitest'
import { createRoot } from 'react-dom/client'
import { act } from 'react'
import ErrorBoundary from '../components/ErrorBoundary'

globalThis.IS_REACT_ACT_ENVIRONMENT = true

function Boom() {
  throw new Error('secret-technical-detail')
}

describe('ErrorBoundary', () => {
  afterEach(() => vi.restoreAllMocks())

  it('shows a Thai message with no technical details when a child throws', () => {
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {})
    const el = document.createElement('div')
    document.body.appendChild(el)
    const root = createRoot(el)
    act(() => root.render(<ErrorBoundary><Boom /></ErrorBoundary>))
    expect(el.textContent).toContain('เกิดข้อผิดพลาดบางอย่าง กรุณาลองใหม่อีกครั้ง')
    expect(el.textContent).not.toContain('secret-technical-detail')
    expect(el.textContent).not.toMatch(/at Boom|Error:/)
    expect(el.querySelector('button')).not.toBeNull()
    expect(spy).toHaveBeenCalled()
    act(() => root.unmount())
  })
})
