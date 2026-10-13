import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0', // allow LAN access during team integration (bind all interfaces)
    port: 5173,
    strictPort: true, // fail fast instead of silently switching ports — nginx proxies to :5173 specifically
    // Accept any Host header: requests arrive via nginx (Host: <LAN IP>) or a
    // Cloudflare Tunnel (Host: <random>.trycloudflare.com), neither of which is
    // known ahead of time. See CVE-2025-24010 — Vite blocks unrecognized Host
    // headers by default; this disables that check for this temporary setup.
    allowedHosts: true,
  },
  test: {
    environment: 'jsdom',
    globals: true,
    env: { VITE_MOCK_MODE: 'false' },
  },
})