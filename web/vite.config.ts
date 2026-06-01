import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// GitLab Pages serves from project URL subpath unless using custom domain.
// Set VITE_BASE_PATH=/your-group/project-midas/ in CI or .env for production.
const base = process.env.VITE_BASE_PATH || '/';

export default defineConfig({
  base,
  plugins: [react()],
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
});
