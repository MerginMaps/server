// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { NodeGlobalsPolyfillPlugin } from '@esbuild-plugins/node-globals-polyfill'
// import { NodeModulesPolyfillPlugin } from '@esbuild-plugins/node-modules-polyfill'
import vue from '@vitejs/plugin-vue2'
import { resolve } from 'path'
import { VuetifyResolver } from 'unplugin-vue-components/resolvers'
import Components from 'unplugin-vue-components/vite'
import { defineConfig } from 'vite'
// import vuetify from 'vite-plugin-vuetify'

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
      resolvers: [VuetifyResolver()]
    }) /*, vuetify() */
  ],

  resolve: {
    alias: {
      '@': resolve(__dirname, './src'),
      // 'vue-i18n': 'vue-i18n/dist/vue-i18n.cjs.js',
      // buffer: 'buffer/',
      events: 'events',
      https: 'agent-base',
      // http: 'stream-http',
      // https: 'https-browserify',
      path: 'path-browserify',
      url: 'url/'
    },
    dedupe: ['vue', 'pinia', 'vue-router', 'vuetify', '@mergin/lib']
  },
  // define: {
  //   'process.env': process.env
  // },
  build: {
    // commonjsOptions: {
    //   include: [/node_modules/],
    //   transformMixedEsModules: true
    // },
    sourcemap: mode !== 'production'
  },
  optimizeDeps: {
    exclude: ['vue', '@mergin'],
    esbuildOptions: {
      define: {
        global: 'globalThis'
      },
      plugins: [
        NodeGlobalsPolyfillPlugin({
          process: true,
          buffer: true
        })
        // NodeModulesPolyfillPlugin()
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
