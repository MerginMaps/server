import { NodeGlobalsPolyfillPlugin } from '@esbuild-plugins/node-globals-polyfill'
import { NodeModulesPolyfillPlugin } from '@esbuild-plugins/node-modules-polyfill'
import vue from '@vitejs/plugin-vue2'
import { resolve } from 'path'
import rollupNodePolyFill from 'rollup-plugin-node-polyfills'
import { VuetifyResolver } from 'unplugin-vue-components/resolvers'
import Components from 'unplugin-vue-components/vite'
import { defineConfig } from 'vite'
import { viteStaticCopy } from 'vite-plugin-static-copy'
// import dts from 'vite-plugin-dts'
// import vuetify from 'vite-plugin-vuetify'

import packageJson from './package.json'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  plugins: [
    vue(),
    Components({
      resolvers: [VuetifyResolver()]
    }) /*, vuetify() */ /*, dts() */,
    viteStaticCopy({
      // copy sass files to use in other applications
      targets: [{ src: 'src/sass/**.scss', dest: 'sass' }]
    })
  ],
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
        // Enable rollup polyfills plugin
        // used during production bundling
        rollupNodePolyFill()
      ]
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
        }),
        NodeModulesPolyfillPlugin()
      ]
    }
  },
  server: {
    watch: {
      ignored: ['!**/node_modules/@mergin/**']
    }
  }
}))
