// User-facing text for login failures; other codes (e.g. NETWORK_ERROR) fall back to err.message.
export function loginErrorMessage(err) {
  if (err.code === 'INVALID_CREDENTIALS') return 'อีเมลหรือรหัสผ่านไม่ถูกต้อง กรุณาลองใหม่อีกครั้ง'
  return err.message
}
