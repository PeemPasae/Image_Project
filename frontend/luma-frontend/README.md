# LUMA Frontend

React + Vite client for the LUMA AI Image Generation System. Talks to the Backend only, via `/api/v1/*`.

## Setup

```bash
npm install
cp .env.example .env   # edit VITE_API_BASE_URL if needed
npm run dev
```

Opens at `http://localhost:5173`. `vite.config.js` binds to `0.0.0.0` so teammates on the same
LAN can also reach it at `http://192.168.1.10:5173` during integration.

## Dev Preview Mode (no Backend needed)

Set `VITE_MOCK_MODE=true` in `.env` to browse every page — Home, Generate, Result, History,
Profile, Setting — with realistic fake data instead of hitting a real Backend. Login/Register
accept anything and log you in as `preview@luma.dev`. A yellow banner shows whenever this is on
so it's never mistaken for live data. Set it back to `false` once the real Backend is ready —
no other code changes needed, every mock response mirrors the real `{success,data}` contract shape.

## Structure

```
src/
  api/client.js        Central axios client — envelope unwrapping, JWT header, 90s generate timeout
  context/AuthContext   token/user state, login/register/logout, restores session from localStorage
  components/           ProtectedRoute, Layout (sidebar shell), AuthImage (fetches auth'd images as blobs)
  pages/                Login, Register, Home, Generate, Result, History, Profile, Setting
  styles/                theme.css (design tokens), layout.css, auth.css, pages.css
```

## Contract notes (do not change without flagging)

- Every response is `{ success, data }` or `{ success, error }`. The client unwraps this —
  page code only ever sees the resolved data or a thrown `Error` with `.code` / `.message`.
- `POST /generate` returns `image_url`, not Base64. Images are fetched as authenticated blobs
  via `AuthImage` / `api.getImageBlob()` since `<img src>` can't send an `Authorization` header.
- JWT is stored in `localStorage` (`luma_token`). A `401 UNAUTHORIZED` response anywhere triggers
  an automatic logout + redirect to `/login` (see the response interceptor in `api/client.js`).
- "Generate Again" only pre-fills the Generate form via router state — it does not call the API.
- Setting (Appearance + Generation Defaults) is `localStorage`-only in V1, no backend persistence.
- Change Password is not implemented in V1 (no endpoint yet) — the button is disabled.

## Not done yet — wires up once Backend is live

- Values in `.env` point at `localhost:5000` by default; switch to the LAN IP for integration.
- No mock server — pages will show network errors until the Backend endpoints exist. That's expected.
