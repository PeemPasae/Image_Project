import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0', // allow LAN access during team integration (bind all interfaces)
    port: 5173,
    strictPort: true, // fail fast instead of silently switching ports — nginx proxies to :5173 specifically
    // Accept any Host header: requests arrive via nginx (Host: 172.20.57.0) or a
    // Cloudflare Tunnel (Host: <random>.trycloudflare.com), neither of which is
    // known ahead of time. See CVE-2025-24010 — Vite blocks unrecognized Host
    // headers by default; this disables that check for this temporary setup.
    allowedHosts: true,
    // HMR over the LAN nginx entry (http://172.20.57.0/) only: the browser's HMR
    // client is told to open its websocket back to 172.20.57.0:80, which nginx's
    // `location /` (with the Upgrade/Connection headers already in place) forwards
    // to this dev server. That address is unreachable from outside the LAN, so
    // anyone coming in through the Cloudflare Tunnel simply can't complete the HMR
    // handshake — the page still loads and works over plain HTTP either way, it
    // just won't hot-reload for those users; refresh the page by hand instead.
    hmr: {
      host: '172.20.57.0',
      protocol: 'ws',
      clientPort: 80,
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    env: { VITE_MOCK_MODE: 'false' },
  },
})