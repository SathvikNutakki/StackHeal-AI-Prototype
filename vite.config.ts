import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // Proxy /analyze and other API calls to FastAPI so you never hit CORS issues
    proxy: {
      '/analyze': 'http://localhost:8000',
      '/health':  'http://localhost:8000',
      '/history': 'http://localhost:8000',
    },
  },
})
