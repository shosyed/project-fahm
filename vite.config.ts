import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { viteStaticCopy } from 'vite-plugin-static-copy'

export default defineConfig({
  plugins: [
    react(),
    viteStaticCopy({
      targets: [
        {
          // stripBase:true flattens the source path so the file lands at dist/sql-wasm.wasm.
          // Without it, viteStaticCopy preserves the full source hierarchy and outputs to
          // dist/node_modules/sql.js/dist/sql-wasm.wasm — present locally only because
          // public/sql-wasm.wasm happens to exist, but missing on Cloudflare (gitignored).
          src: 'node_modules/sql.js/dist/sql-wasm.wasm',
          dest: '.',
          rename: { stripBase: true },
        },
      ],
    }),
  ],
  server: {
    headers: {
      'Cross-Origin-Opener-Policy': 'same-origin',
      'Cross-Origin-Embedder-Policy': 'require-corp',
    },
  },
  optimizeDeps: {
    exclude: ['@mlc-ai/web-llm'],
  },
  build: {
    chunkSizeWarningLimit: 10000,
  },
})
