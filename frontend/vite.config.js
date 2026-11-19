import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: Object.fromEntries(
      ['/api', '/videos', '/exportados', '/temp_clip_cache'].map(path => [path, 'http://127.0.0.1:8765'])
    ),
  },
})
