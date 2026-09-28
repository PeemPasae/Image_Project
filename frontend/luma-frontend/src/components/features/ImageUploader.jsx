import { useEffect, useRef, useState } from 'react'
import { useToast } from '../../context/ToastContext'

export const ACCEPTED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp']
export const NO_IMAGE_MESSAGE = 'No image yet — JPG, PNG, or WEBP.'
const REJECT_MESSAGE = 'Please upload a JPG, PNG, or WEBP image.'

// Shared pick/validate/preview-URL lifecycle for the button below and its
// sibling dropzone (ImageDropzone) — both funnel through this one hook so
// there's a single object URL owner no matter which path the file came in
// from: created once per valid pick, the previous one revoked before that,
// and revoked again on unmount.
export function useImagePicker(onChange) {
  const { showToast } = useToast()
  const urlRef = useRef('')

  useEffect(() => () => {
    if (urlRef.current) URL.revokeObjectURL(urlRef.current)
  }, [])

  return function pick(picked) {
    if (!picked) return
    if (!ACCEPTED_IMAGE_TYPES.includes(picked.type)) {
      showToast(REJECT_MESSAGE, 'error')
      return
    }
    if (urlRef.current) URL.revokeObjectURL(urlRef.current)
    const nextUrl = URL.createObjectURL(picked)
    urlRef.current = nextUrl
    onChange(picked, nextUrl)
  }
}

// "Choose/Change image" button shared by every image tool. Purely a native
// file-input trigger — validation and the preview URL's lifecycle live in
// useImagePicker above, shared with ImageDropzone.
export default function ImageUploader({ file, onPick, className = 'btn btn-ghost spot-blur-file' }) {
  function handleChange(e) {
    const picked = e.target.files?.[0]
    e.target.value = '' // allow re-picking the same file
    onPick(picked)
  }

  return (
    <label className={className}>
      {file ? 'Change image' : 'Choose image'}
      <input type="file" accept={ACCEPTED_IMAGE_TYPES.join(',')} onChange={handleChange} hidden />
    </label>
  )
}

// Empty-state dropzone every tool shows before an image is picked — same
// onPick path (and so the same validation/toast/preview-URL handling) as
// the button above, plus real HTML5 drag-and-drop onto the box itself.
export function ImageDropzone({ onPick, className = 'spot-blur-empty' }) {
  const [isDragOver, setIsDragOver] = useState(false)

  function handleDragOver(e) {
    e.preventDefault() // required — without it the browser opens the file instead of allowing a drop
    setIsDragOver(true)
  }

  function handleDrop(e) {
    e.preventDefault()
    setIsDragOver(false)
    onPick(e.dataTransfer.files?.[0])
  }

  return (
    <div
      className={`${className}${isDragOver ? ' is-drag-over' : ''}`}
      onDragOver={handleDragOver}
      onDragLeave={() => setIsDragOver(false)}
      onDrop={handleDrop}
    >
      {NO_IMAGE_MESSAGE}
    </div>
  )
}
