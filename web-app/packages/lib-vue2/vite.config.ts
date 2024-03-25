// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { NodeGlobalsPolyfillPlugin } from '@esbuild-plugins/node-globals-polyfill'
import vue from '@vitejs/plugin-vue2'
import { resolve } from 'path'
import rollupNodePolyFill from 'rollup-plugin-node-polyfills'
import { VuetifyResolver } from 'unplugin-vue-components/resolvers'
import Components from 'unplugin-vue-components/vite'
import { defineConfig } from 'vite'
import { viteStaticCopy } from 'vite-plugin-static-copy'
// import vuetify from 'vite-plugin-vuetify'

import packageJson from './package.json'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  plugins: [
    vue(),
    Components({
      resolvers: [VuetifyResolver()]
    }),
    viteStaticCopy({
      // copy sass files to use in other applications
      targets: [{ src: 'src/sass/**.scss', dest: 'sass' }]
    })
  ],
  publicDir: './src/assets',
  css: {
    preprocessorOptions: {
      scss: {
        quietDeps: true
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
    dedupe: ['vue', 'pinia', 'vue-router', 'vuetify']
  },
  build: {
    commonjsOptions: {
      //   include: [/node_modules/],
      transformMixedEsModules: true
    },
    sourcemap: mode !== 'production',
    lib: {
      // Could also be a dictionary or array of multiple entry points
      entry: resolve(__dirname, 'src/main.ts'),
      name: 'lib',
      // the proper extensions will be added
      fileName: 'lib'
    },
    rollupOptions: {
      // make sure to externalize deps that shouldn't be bundled
      // into your library
      external: [
        'vue',
        'pinia',
        ...Object.keys(packageJson.dependencies),
        '@vue/babel-helper-vue-jsx-merge-props'
      ],
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
