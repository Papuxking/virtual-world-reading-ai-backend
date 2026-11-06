import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import process from 'node:process'

const apiTarget = process.env.VITE_API_PROXY_TARGET || 'http://api:8000';

// https://vite.dev/config/
export default defineConfig({
  base: '/dashboard/',
  plugins: [react()],
  server: {
    proxy: {
      '/auth': {
        target: apiTarget,
        changeOrigin: true,
      },
      '/admin': {
        target: apiTarget,
        changeOrigin: true,
      },
      '/health': {
        target: apiTarget,
        changeOrigin: true,
      },
      '/achievements': {
        target: apiTarget,
        changeOrigin: true,
      },
      '/leaderboard': {
        target: apiTarget,
        changeOrigin: true,
      },
      '/comics': {
        target: apiTarget,
        changeOrigin: true,
      },
      '/evaluation': {
        target: apiTarget,
        changeOrigin: true,
      },
      '/static': {
        target: apiTarget,
        changeOrigin: true,
      },
    },
  },
})
