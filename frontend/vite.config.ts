// frontend/vite.config.ts
//
// Vite bundler configuration.
//
// Key settings:
//   - react plugin: enables JSX transform and Fast Refresh in dev mode
//   - server.proxy: during local development (npm run dev), requests to /api
//     are forwarded to the FastAPI backend at localhost:8000.  This mirrors
//     what Nginx does in the Docker container setup.

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],

  server: {
    port: 5173,   // Default Vite dev server port
    proxy: {
      // In development, proxy /api/* to the backend
      // so you don't need to set CORS headers manually.
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,   // Rewrites the Host header to the target
      },
    },
  },

  build: {
    outDir: 'dist',              // Nginx serves from /usr/share/nginx/html/dist → mapped here
    sourcemap: false,            // Disable source maps in production (reduce bundle size)
  },
})
