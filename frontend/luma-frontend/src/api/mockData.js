// Dev Preview Mode data — mirrors the real API contract exactly so switching
// back to a live Backend later requires no changes to page code.

function placeholderImage(seedText) {
  // Deterministic-ish flat-color SVG so each mock generation looks distinct,
  // with zero network dependency and zero copyright concerns.
  let hash = 0
  for (let i = 0; i < seedText.length; i++) hash = (hash * 31 + seedText.charCodeAt(i)) >>> 0
  const hue = hash % 360
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512">
    <rect width="512" height="512" fill="hsl(${hue},55%,22%)"/>
    <circle cx="256" cy="256" r="120" fill="hsl(${(hue + 40) % 360},60%,45%)" opacity="0.6"/>
  </svg>`
  return `data:image/svg+xml;base64,${btoa(svg)}`
}

export const MOCK_USER = { id: 1, email: 'preview@luma.dev' }

export const MOCK_MODELS = [
  { title: 'anypastel', model_name: 'anypastel' },
  { title: 'realisticVision', model_name: 'realisticVision' },
]

export const MOCK_GENERATIONS = [
  {
    id: 1, generation_id: 1,
    prompt: 'A beautiful girl standing in a cyberpunk city, neon lights, cinematic lighting',
    negative_prompt: 'blurry, low quality, bad anatomy',
    checkpoint: 'anypastel', sampler: 'DPM++ 2M Karras',
    width: 512, height: 512, steps: 20, cfg_scale: 7, seed: 123456789,
    created_at: '2026-08-24T16:30:00',
  },
  {
    id: 2, generation_id: 2,
    prompt: 'A quiet mountain village at dawn, soft golden light, mist over the valley, wide shot, painterly style, highly detailed',
    negative_prompt: '',
    checkpoint: 'realisticVision', sampler: 'Euler a',
    width: 768, height: 768, steps: 30, cfg_scale: 9.5, seed: 987654321,
    created_at: '2026-08-25T09:12:00',
  },
  {
    id: 3, generation_id: 3,
    prompt: 'Portrait of a robot',
    negative_prompt: 'extra limbs, watermark',
    checkpoint: 'anypastel', sampler: 'Euler',
    width: 1024, height: 1024, steps: 20, cfg_scale: 7, seed: 555,
    created_at: '2026-08-26T14:05:00',
  },
]

export const MOCK_PROFILE = {
  id: 1,
  email: MOCK_USER.email,
  created_at: '2026-08-20T10:00:00',
  generation_count: MOCK_GENERATIONS.length,
}

export function mockImageUrlFor(id) {
  const gen = MOCK_GENERATIONS.find((g) => g.id === Number(id))
  return placeholderImage(gen ? gen.prompt : String(id))
}

/** Small artificial delay so loading states are visible while browsing. */
export function delay(ms = 350) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}
