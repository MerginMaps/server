// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { NodeGlobalsPolyfillPlugin } from '@esbuild-plugins/node-globals-polyfill'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'
import { PrimeVueResolver } from 'unplugin-vue-components/resolvers'
import Components from 'unplugin-vue-components/vite'
import { defineConfig, splitVendorChunkPlugin } from 'vite'

const serverPort = process.env.FLASK_RUN_PORT ?? 5000

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  base:
    mode === 'production' && process.env.PUBLIC_PATH
      ? process.env.PUBLIC_PATH
      : '/',
  plugins: [
    vue(),
    Components({
      resolvers: [PrimeVueResolver({ prefix: 'P' })]
    }),
    splitVendorChunkPlugin()
  ],

  css: {
    preprocessorOptions: {
      sass: {
        quietDeps: true
      }
    }
  },

  resolve: {
    alias: {
      '@': resolve(__dirname, './src'),
      // 'vue-i18n': 'vue-i18n/dist/vue-i18n.cjs.js',
      url: 'rollup-plugin-node-polyfills/polyfills/url'
    },
    dedupe: [
      'vue',
      'pinia',
      'vue-router',
      'vuetify',
      'primevue',
      '@mergin/lib',
      '@mergin/admin-lib'
    ]
  },
  build: {
    sourcemap: mode !== 'production'
  },
  optimizeDeps: {
    exclude: ['vue', '@mergin', 'vue-demi'],
    esbuildOptions: {
      define: {
        global: 'globalThis'
      },
      plugins: [
        NodeGlobalsPolyfillPlugin({
          process: false,
          buffer: false
        })
      ]
    }
    // include: ['linked-dep', 'node_modules']
  },
  server: {
    proxy: {
      '/v1': {
        target: `http://127.0.0.1:${serverPort}`
      },
      '/v2': {
        target: `http://127.0.0.1:${serverPort}`
      },
      '/app': {
        target: `http://127.0.0.1:${serverPort}`
      },
      '/ping': {
        target: `http://127.0.0.1:${serverPort}`
      },
      '/config': {
        target: `http://127.0.0.1:${serverPort}`
      }
    },
    watch: {
      ignored: ['!**/node_modules/@mergin/**']
    }
  }
}))
