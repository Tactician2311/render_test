import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  // Base URL for the built frontend assets
  base: '/',
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
})
