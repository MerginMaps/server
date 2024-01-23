// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import vue from '@vitejs/plugin-vue2'
import { resolve } from 'path'
import { VuetifyResolver } from 'unplugin-vue-components/resolvers'
import Components from 'unplugin-vue-components/vite'
import { defineConfig } from 'vite'
// import vuetify from 'vite-plugin-vuetify'

import packageJson from './package.json'

export default defineConfig(({ mode }) => ({
  plugins: [
    vue(),
    Components({
      resolvers: [VuetifyResolver()]
    }) /*, vuetify() */
  ],
  publicDir: './src/assets',
  css: {
    preprocessorOptions: {
      sass: {
        quietDeps: true
      }
    }
  },

  resolve: {
    alias: {
      '@': resolve(__dirname, './src')
    },
    dedupe: ['vue', 'pinia', 'vue-router', 'vuetify', '@mergin/lib-vue2']
  },
  build: {
    sourcemap: mode !== 'production',
    lib: {
      // Could also be a dictionary or array of multiple entry points
      entry: resolve(__dirname, 'src/main.ts'),
      name: 'admin-lib',
      // the proper extensions will be added
      fileName: 'admin-lib'
    },
    rollupOptions: {
      // make sure to externalize deps that shouldn't be bundled
      // into your library
      external: [
        'vue',
        'pinia',
        ...Object.keys(packageJson.dependencies),
        '@mergin/lib-vue2',
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
      }
    }
  },
  optimizeDeps: {
    exclude: ['vue', '@mergin'],
    esbuildOptions: {
      define: {
        global: 'globalThis'
      }
    }
  },
  server: {
    watch: {
      ignored: ['!**/node_modules/@mergin/**']
    }
  }
}))
