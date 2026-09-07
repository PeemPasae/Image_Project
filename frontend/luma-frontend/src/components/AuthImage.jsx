import { useEffect, useState } from 'react'
import { api } from '../api/client'

/**
 * /api/v1/images/:id returns raw binary and requires a JWT header, so a plain
 * <img src="..."> can't be used directly. This fetches it as a Blob and
 * renders an object URL instead. Cleans up the URL on unmount.
 */
export default function AuthImage({ imageUrl, alt = '', className = '' }) {
  const [src, setSrc] = useState(null)
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    let objectUrl
    let cancelled = false
    setFailed(false)
    setSrc(null)

    if (!imageUrl) return

    api.getImageBlob(imageUrl)
      .then((url) => {
        if (cancelled) return
        objectUrl = url
        setSrc(url)
      })
      .catch(() => {
        if (!cancelled) setFailed(true)
      })

    return () => {
      cancelled = true
      if (objectUrl) URL.revokeObjectURL(objectUrl)
    }
  }, [imageUrl])

  if (failed) {
    return <div className={`auth-image-fallback ${className}`}>Image unavailable</div>
  }
  if (!src) {
    return <div className={`auth-image-fallback ${className}`}><span className="spinner" /></div>
  }
  return <img src={src} alt={alt} className={className} />
}
