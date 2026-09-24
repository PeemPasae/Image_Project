import { useEffect, useRef } from 'react'
import { useToast } from '../../context/ToastContext'

export const ACCEPTED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp']
export const NO_IMAGE_MESSAGE = 'No image yet — JPG, PNG, or WEBP.'

// Upload button shared by every image tool: validates the file type and owns
// the preview object URL's lifecycle (creates one per pick, revokes the
// previous one, revokes on unmount). The caller still keeps its own
// file/previewUrl state — it needs both for its own processing/reset logic —
// this just hands the picked {file, previewUrl} up via onChange.
export default function ImageUploader({ file, onChange, className = 'btn btn-ghost spot-blur-file' }) {
  const { showToast } = useToast()
  const urlRef = useRef('')

  useEffect(() => () => {
    if (urlRef.current) URL.revokeObjectURL(urlRef.current)
  }, [])

  function handleChange(e) {
    const picked = e.target.files?.[0]
    e.target.value = '' // allow re-picking the same file
    if (!picked) return
    if (!ACCEPTED_IMAGE_TYPES.includes(picked.type)) {
      showToast('Please upload a JPG, PNG, or WEBP image.', 'error')
      return
    }
    if (urlRef.current) URL.revokeObjectURL(urlRef.current)
    const nextUrl = URL.createObjectURL(picked)
    urlRef.current = nextUrl
    onChange(picked, nextUrl)
  }

  return (
    <label className={className}>
      {file ? 'Change image' : 'Choose image'}
      <input type="file" accept={ACCEPTED_IMAGE_TYPES.join(',')} onChange={handleChange} hidden />
    </label>
  )
}
