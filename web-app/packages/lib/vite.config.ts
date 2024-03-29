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
export default defineConfig(() => ({
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
      //   include: [/node_modules/],
      transformMixedEsModules: true
    },
    // Fix for watching, if watch:lib, disable this
    // sourcemap: mode !== 'production',
    sourcemap: false,
    lib: {
      formats: ['es'],
      // Could also be a dictionary or array of multiple entry points
      entry: resolve(__dirname, 'src/main.ts'),
      name: 'lib',
      // the proper extensions will be added
      fileName: 'lib'
    },
    rollupOptions: {
      // make sure to externalize deps that shouldn't be bundled
      // into your library
      external: ['vue', 'pinia', ...Object.keys(packageJson.dependencies)],
      output: {
        exports: 'named',
        // Provide global variables to use in the UMD build
        // for externalized deps
        globals: {
          vue: 'Vue',
          pinia: 'pinia'
        }
      },
      plugins: [
        // Enable rollup polyfills plugin
        // used during production bundling
        rollupNodePolyFill()
      ]
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
}))
