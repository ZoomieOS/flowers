import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// base './' — чтобы страница работала с любого статического хостинга и из подпапки
export default defineConfig({
  base: './',
  plugins: [react()],
})
