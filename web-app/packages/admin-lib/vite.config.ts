import { NodeGlobalsPolyfillPlugin } from '@esbuild-plugins/node-globals-polyfill'
// import { NodeModulesPolyfillPlugin } from '@esbuild-plugins/node-modules-polyfill'
import vue from '@vitejs/plugin-vue2'
import { resolve } from 'path'
import { defineConfig } from 'vite'
// import vuetify from 'vite-plugin-vuetify'

import packageJson from './package.json'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  plugins: [vue() /*, vuetify() */],
  publicDir: './src/assets',

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
      }
    }
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
  },
  server: {
    watch: {
      ignored: ['!**/node_modules/@mergin/**']
    }
  }
}))
