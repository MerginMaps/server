import { NodeGlobalsPolyfillPlugin } from '@esbuild-plugins/node-globals-polyfill'
// import { NodeModulesPolyfillPlugin } from '@esbuild-plugins/node-modules-polyfill'
import vue from '@vitejs/plugin-vue'
// import { copy } from '@web/rollup-plugin-copy'
import { join, resolve } from 'path'
import copy from 'rollup-plugin-copy'
import { defineConfig } from 'vite'
import vuetify from 'vite-plugin-vuetify'

import packageJson from './package.json'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  plugins: [vue(), vuetify()],

  resolve: {
    alias: {
      '@': resolve(__dirname, './src'),
      // buffer: 'buffer/',
      events: 'events',
      https: 'agent-base',
      // http: 'stream-http',
      // https: 'https-browserify',
      path: 'path-browserify',
      url: 'url/'
    }
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
      external: ['vue', ...Object.keys(packageJson.dependencies)],
      output: {
        exports: 'named',
        // Provide global variables to use in the UMD build
        // for externalized deps
        globals: {
          vue: 'Vue'
        }
      },
      plugins: [
        copy({
          targets: [
            {
              src: join(__dirname, 'src/assets'),
              dest: join(__dirname, 'src/assets')
            },
            {
              src: join(__dirname, 'src/saas'),
              dest: join(__dirname, 'src/saas')
            }
          ]
        })
      ]
    }
  },
  optimizeDeps: {
    exclude: ['vue'],
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
  }
}))
