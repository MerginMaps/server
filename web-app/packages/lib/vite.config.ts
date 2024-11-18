// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { NodeGlobalsPolyfillPlugin } from '@esbuild-plugins/node-globals-polyfill'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'
import rollupNodePolyFill from 'rollup-plugin-node-polyfills'
import { PrimeVueResolver } from 'unplugin-vue-components/resolvers'
import Components from 'unplugin-vue-components/vite'
import { defineConfig } from 'vite'
// import { viteStaticCopy } from 'vite-plugin-static-copy'

import packageJson from './package.json'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    Components({
      resolvers: [
        PrimeVueResolver({
          prefix: 'P'
        })
      ]
    })
  ],
  publicDir: './src/assets',

  css: {
    preprocessorOptions: {
      scss: {
        additionalData: `@import "primeflex/core/_variables.scss";`
      }
    }
  },

  resolve: {
    alias: {
      '@': resolve(__dirname, './src'),
      events: 'rollup-plugin-node-polyfills/polyfills/events',
      https: 'agent-base',
      path: 'rollup-plugin-node-polyfills/polyfills/path'
    },
    dedupe: ['vue', 'pinia', 'vue-router']
  },
  build: {
    commonjsOptions: {
      transformMixedEsModules: true
    },
    sourcemap: false,
    lib: {
      formats: ['es'],
      entry: resolve(__dirname, 'src/main.ts'),
      name: 'lib',
      fileName: 'lib'
    },
    rollupOptions: {
      external: ['vue', 'pinia', ...Object.keys(packageJson.dependencies)],
      output: {
        exports: 'named',
        globals: {
          vue: 'Vue',
          pinia: 'pinia'
        }
      },
      plugins: [rollupNodePolyFill()]
    }
  },
  optimizeDeps: {
    exclude: ['vue', '@mergin', 'vue-demi'],
    esbuildOptions: {
      define: {
        global: 'globalThis'
      },
      plugins: [
        NodeGlobalsPolyfillPlugin({
          process: true,
          buffer: true
        })
      ]
    }
  },
  server: {
    watch: {
      ignored: ['!**/node_modules/@mergin/**']
    }
  }
})
