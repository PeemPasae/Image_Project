// Dev Preview Mode data — mirrors the real API contract exactly so switching
// back to a live Backend later requires no changes to page code.

function placeholderImage(seedText) {
  // Gradient placeholder ที่อยู่ในจานสีของ design system (Primary ↔ Secondary)
  // deterministic, ไม่พึ่ง network, ไม่มีปัญหาลิขสิทธิ์
  let hash = 0
  for (let i = 0; i < seedText.length; i++) hash = (hash * 31 + seedText.charCodeAt(i)) >>> 0

  const PALETTE = [
    ['#A78BFA', '#8B5CF6'], // Primary Light → Primary
    ['#93C5FD', '#5EB1FF'], // Secondary Light → Secondary
    ['#C4B5FD', '#93C5FD'],
    ['#8B5CF6', '#5EB1FF'], // brand gradient
  ]
  const [from, to] = PALETTE[hash % PALETTE.length]
  const cx = 140 + (hash % 240)

  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512">
    <defs>
      <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0" stop-color="${from}"/>
        <stop offset="1" stop-color="${to}"/>
      </linearGradient>
    </defs>
    <rect width="512" height="512" fill="url(#g)"/>
    <circle cx="${cx}" cy="150" r="170" fill="#FFFFFF" opacity="0.18"/>
    <circle cx="${512 - cx}" cy="400" r="130" fill="#FFFFFF" opacity="0.12"/>
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
