import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5000,
    allowedHosts: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/generate': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/transcripts': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/transcript': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    }
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})
