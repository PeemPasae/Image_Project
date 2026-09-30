import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// export default defineConfig({
//   plugins: [react()],
//   server: {
//     host: true, // allow LAN access during team integration (192.168.1.10)
//     port: 5173,
//   },
// })

export default defineConfig({
  plugins: [react()],
  server: {
    // dev server รับเฉพาะ localhost — หน้าเว็บของจริงเสิร์ฟผ่าน nginx จาก dist/ (ดู nginx/README.md)
    // อยากให้เพื่อนเปิด dev server จากเครื่องอื่นชั่วคราว: `npm run dev -- --host`
    host: 'localhost',
    port: 5173,
  },
  test: {
    environment: 'jsdom',
    globals: true,
  },
})