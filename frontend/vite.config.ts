import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id: string) {
          if (id.includes('node_modules')) {
            if (id.includes('echarts') || id.includes('@ant-design/charts')) {
              return 'charts'
            }
            if (id.includes('@antv')) {
              return 'antv'
            }
            if (id.includes('antd') || id.includes('@ant-design/icons')) {
              return 'antd'
            }
            if (id.includes('react') || id.includes('react-router') || id.includes('react-dom')) {
              return 'react-vendor'
            }
            if (id.includes('redux') || id.includes('@reduxjs')) {
              return 'redux'
            }
            if (id.includes('axios')) {
              return 'axios'
            }
            if (id.includes('dayjs')) {
              return 'dayjs'
            }
            return 'vendor'
          }
        },
      },
    },
  },
})
