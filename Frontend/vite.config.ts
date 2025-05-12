import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import fs from 'fs';
import type { ServerOptions } from 'https';

// Get HTTPS configuration based on environment
const getHttpsConfig = (): ServerOptions | undefined => {
  try {
    return {
      key: fs.readFileSync('../certs/server.key'),
      cert: fs.readFileSync('../certs/server.crt')
    };
  } catch (error) {
    console.warn('SSL certificates not found, HTTPS will not be available in dev mode');
    return undefined; 
  }
};

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  base: process.env.ELECTRON === "true" ? './' : '/',
  server: {
    port: 3000,
    strictPort: true,
    host: true,
    https: process.env.NODE_ENV === 'production' ? undefined : getHttpsConfig(),
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    rollupOptions: {
      input: {
        main: path.resolve(__dirname, 'index.html')
      }
    }
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  optimizeDeps: {
    exclude: ['electron']
  }
});