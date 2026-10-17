import { defineConfig } from 'vite';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  plugins: [tailwindcss()],
  server: {
    port: 5173,
    // Forward /api to Flask so the browser sees a single origin in development.
    proxy: {
      '/api': 'http://localhost:5000',
    },
  },
});
