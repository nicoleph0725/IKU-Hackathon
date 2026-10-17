import { defineConfig } from 'vite';

import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  plugins: [tailwindcss()],
  // Read environment variables from backend/.env so the team keeps one .env file.
  envDir: '../backend',
  // Only variables starting with these prefixes are given to the browser code.
  // Everything else in .env (like SECRET_KEY) stays private to the backend.
  envPrefix: ['VITE_', 'MAP_'],
  server: {
    // Requests to /api go to the Flask backend.
    proxy: { '/api': 'http://localhost:5000' },
  },
});
