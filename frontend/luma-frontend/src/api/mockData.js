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

// role: 'admin' only exists here so the admin page is browsable in mock mode.
export const MOCK_USER = { id: 1, email: 'preview@luma.dev', role: 'admin' }

// Fake user list for the admin page. Deleting removes from this in-memory list
// for the rest of the session (a page reload resets it).
const INITIAL_ADMIN_USERS = [
  { id: 1, email: 'preview@luma.dev', created_at: '2026-08-20T10:00:00', generation_count: 3 },
  { id: 2, email: 'somchai@example.com', created_at: '2026-08-22T09:15:00', generation_count: 12 },
  { id: 3, email: 'nattaya@example.com', created_at: '2026-08-25T13:40:00', generation_count: 0 },
  { id: 4, email: 'preecha@example.com', created_at: '2026-09-01T18:05:00', generation_count: 27 },
  { id: 5, email: 'malee@example.com', created_at: '2026-09-03T11:30:00', generation_count: 5 },
  { id: 6, email: 'anan@example.com', created_at: '2026-09-10T08:00:00', generation_count: 1 },
]
let mockAdminUsers = INITIAL_ADMIN_USERS.map((u) => ({ ...u }))

export function listMockAdminUsers() {
  return mockAdminUsers.map((u) => ({ ...u }))
}

export function deleteMockAdminUser(id) {
  mockAdminUsers = mockAdminUsers.filter((u) => String(u.id) !== String(id))
}

export function resetMockAdminUsers() {
  mockAdminUsers = INITIAL_ADMIN_USERS.map((u) => ({ ...u }))
}

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

// Mirrors backend/app/services/image_filters/gesture.py's _format() shape —
// a single detected "Thumb_Up" hand, same field names/ranges as the real API
// (confidence 0-100, 21 landmarks).
export const MOCK_GESTURE_RESULT = {
  found: true,
  hand_count: 1,
  gesture: 'Thumb_Up',
  gesture_th: 'ชูนิ้วโป้ง',
  confidence: 92.5,
  handedness: 'Right',
  inference_time_ms: 42.3,
  hands: [
    {
      gesture: 'Thumb_Up',
      gesture_th: 'ชูนิ้วโป้ง',
      confidence: 92.5,
      handedness: 'Right',
      landmarks: Array.from({ length: 21 }, (_, i) => ({
        x: 0.42 + (i % 5) * 0.02,
        y: 0.3 + Math.floor(i / 5) * 0.05,
      })),
    },
  ],
}

export function mockImageUrlFor(id) {
  const gen = MOCK_GENERATIONS.find((g) => g.id === Number(id))
  return placeholderImage(gen ? gen.prompt : String(id))
}

/** Small artificial delay so loading states are visible while browsing. */
export function delay(ms = 350) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}
