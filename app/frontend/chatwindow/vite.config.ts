import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Vite frontend (app/frontend) — AI girlfriend Talk UI.
// /api/* → app/backend token API; browser then connects to LiveKit.
const backendProxy = process.env.VITE_BACKEND_PROXY || 'http://127.0.0.1:8080'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': {
        target: backendProxy,
        changeOrigin: true,
      },
    },
  },
  preview: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': {
        target: backendProxy,
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
})
