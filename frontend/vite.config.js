import { defineConfig } from 'vite';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  plugins: [tailwindcss()],
  server: {
    // Requests to /api go to the Flask backend.
    proxy: { '/api': 'http://localhost:5000' },
  },
});
