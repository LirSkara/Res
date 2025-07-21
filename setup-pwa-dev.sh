#!/bin/bash

# QRes OS 4 - Скрипт для настройки PWA в режиме разработки
# =========================================================

echo "🔧 Настройка PWA для работы на HTTP в режиме разработки..."

# Создаем локальный vite.config для разработки PWA
cat > /tmp/vite.config.dev.js << 'EOF'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    vue(),
    VitePWA({
      registerType: 'autoUpdate',
      devOptions: {
        enabled: true, // Включаем PWA в режиме разработки
        type: 'module'
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg}']
      },
      manifest: {
        name: 'QRes OS 4 - Waiter Terminal',
        short_name: 'QRes Terminal',
        description: 'Restaurant management system for waiters',
        theme_color: '#007bff',
        background_color: '#ffffff',
        display: 'standalone',
        orientation: 'portrait',
        scope: '/',
        start_url: '/',
        icons: [
          {
            src: '/icon-192x192.png',
            sizes: '192x192',
            type: 'image/png'
          },
          {
            src: '/icon-512x512.png',
            sizes: '512x512',
            type: 'image/png'
          }
        ]
      }
    })
  ],
  server: {
    host: '0.0.0.0', // Слушаем на всех интерфейсах
    port: 4173,
    strictPort: true
  },
  preview: {
    host: '0.0.0.0',
    port: 4173,
    strictPort: true
  }
})
EOF

echo "✅ Конфигурация создана в /tmp/vite.config.dev.js"
echo ""
echo "📋 Для использования:"
echo "1. Скопируйте конфиг: cp /tmp/vite.config.dev.js ~/qresos/terminal/vite.config.js"
echo "2. Перезапустите: npm run preview"
echo "3. Откройте: http://192.168.4.1:4173"
echo ""
echo "🔧 Для отладки PWA:"
echo "1. Откройте DevTools (F12)"
echo "2. Перейдите на вкладку Application"
echo "3. Проверьте Service Workers и Manifest"
