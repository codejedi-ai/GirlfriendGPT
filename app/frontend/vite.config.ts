import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// GirlfriendGPT local stack — frontend talks only to app/backend (not Django).
const BACKEND =
  process.env.VITE_BACKEND_PROXY ||
  process.env.BACKEND_URL ||
  'http://127.0.0.1:8080'

export default defineConfig({
  plugins: [react()],
  server: {
    // true → all interfaces so http://localhost:5173 works (macOS prefers [::1])
    host: true,
    port: 5173,
    strictPort: true,
    proxy: {
      '/api': { target: BACKEND, changeOrigin: true },
    },
  },
  preview: {
    host: true,
    port: 5173,
    strictPort: true,
    proxy: {
      '/api': { target: BACKEND, changeOrigin: true },
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './components'),
      '@contexts': path.resolve(__dirname, './contexts'),
      '@pages': path.resolve(__dirname, './pages'),
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    chunkSizeWarningLimit: 600,
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'framer-motion': ['framer-motion'],
          'mui': ['@mui/material', '@mui/icons-material', '@mui/system', '@emotion/react', '@emotion/styled'],
          'icons': ['lucide-react', 'react-icons'],
        },
      },
    },
  },
})
