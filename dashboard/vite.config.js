import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  base: '/dashboard/',
  plugins: [react()],
  server: {
    proxy: {
      '/auth': {
        target: 'http://api:8000',
        changeOrigin: true,
      },
      '/admin': {
        target: 'http://api:8000',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://api:8000',
        changeOrigin: true,
      },
      '/achievements': {
        target: 'http://api:8000',
        changeOrigin: true,
      },
      '/leaderboard': {
        target: 'http://api:8000',
        changeOrigin: true,
      },
      '/comics': {
        target: 'http://api:8000',
        changeOrigin: true,
      },
      '/static': {
        target: 'http://api:8000',
        changeOrigin: true,
      },
    },
  },
})
