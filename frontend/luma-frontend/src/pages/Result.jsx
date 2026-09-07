import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api } from '../api/client'

export default function Result() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [generation, setGeneration] = useState(null)
  const [imageSrc, setImageSrc] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let objectUrl
    setLoading(true)
    setError('')

    api.getGeneration(id)
      .then(async (data) => {
        setGeneration(data)
        objectUrl = await api.getImageBlob(data.image_url)
        setImageSrc(objectUrl)
      })
      .catch((err) => {
        setError(err.code === 'GENERATION_NOT_FOUND' ? 'This generation was not found.' : err.message)
      })
      .finally(() => setLoading(false))

    return () => { if (objectUrl) URL.revokeObjectURL(objectUrl) }
  }, [id])

  function handleDownload() {
    if (!imageSrc) return
    const a = document.createElement('a')
    a.href = imageSrc
    a.download = `luma-${id}.png`
    a.click()
  }

  function handleGenerateAgain() {
    // Loads the same parameters back into the form — does not auto-generate.
    navigate('/generate', {
      state: {
        prefill: {
          prompt: generation.prompt,
          negative_prompt: generation.negative_prompt,
          checkpoint: generation.checkpoint,
          width: generation.width,
          height: generation.height,
          steps: generation.steps,
          cfg_scale: generation.cfg_scale,
          sampler: generation.sampler,
          seed: -1,
        },
      },
    })
  }

  if (loading) return <div className="empty-state"><span className="spinner" /></div>
  if (error) return <div className="empty-state card">{error}</div>
  if (!generation) return null

  return (
    <div>
      <div className="page-header">
        <h1>Result</h1>
        <p>Generation #{generation.generation_id || id}</p>
      </div>

      <div className="two-col">
        <div className="result-image-wrap">
          {imageSrc && <img src={imageSrc} alt={generation.prompt} />}
        </div>

        <div>
          <div className="param-list card">
            <div className="param-row"><span className="k">Prompt</span><span className="v">{generation.prompt}</span></div>
            <div className="param-row"><span className="k">Negative Prompt</span><span className="v">{generation.negative_prompt || '—'}</span></div>
            <div className="param-row"><span className="k">Model</span><span className="v">{generation.checkpoint}</span></div>
            <div className="param-row"><span className="k">Sampler</span><span className="v">{generation.sampler}</span></div>
            <div className="param-row"><span className="k">Size</span><span className="v">{generation.width}×{generation.height}</span></div>
            <div className="param-row"><span className="k">Steps</span><span className="v">{generation.steps}</span></div>
            <div className="param-row"><span className="k">CFG Scale</span><span className="v">{generation.cfg_scale}</span></div>
            <div className="param-row"><span className="k">Seed</span><span className="v">{generation.seed}</span></div>
            <div className="param-row"><span className="k">Created</span><span className="v">{generation.created_at}</span></div>
          </div>

          <div className="action-row">
            <button className="btn btn-primary" onClick={handleDownload}>Download</button>
            <button className="btn btn-ghost" onClick={handleGenerateAgain}>Generate Again</button>
            <button className="btn btn-ghost" onClick={() => navigate('/history')}>View History</button>
          </div>
        </div>
      </div>
    </div>
  )
}
