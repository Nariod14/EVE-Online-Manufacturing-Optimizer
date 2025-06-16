import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import path from 'path';  // <<<<< Add this import

export default defineConfig({
  plugins: [
    react(),
    tailwindcss()
  ],
  resolve: {   // must be inside resolve, not top-level alias
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
});
