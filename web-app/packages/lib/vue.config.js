const { defineConfig } = require('@vue/cli-service')
const CopyWebpackPlugin = require('copy-webpack-plugin')
const dotenv = require('dotenv')
const dotenvExpand = require('dotenv-expand')
const path = require('path')
const { VuetifyLoaderPlugin } = require('vuetify-loader')
const nodeExternals = require('webpack-node-externals')

const PROJECT_DIR = '../..'
const myEnv = dotenv.config({ path: path.join(PROJECT_DIR, '.env') })
dotenvExpand(myEnv)

const publicPath =
  process.env.NODE_ENV === 'production' && process.env.PUBLIC_PATH
    ? process.env.PUBLIC_PATH ?? '/'
    : '/'

module.exports = defineConfig({
  transpileDependencies: true,
  lintOnSave: false,
  publicPath,
  css: {
    extract: true
  },
  chainWebpack: (config) => {
    // do not inline svg assets
    config.module
      .rule('svg')
      .set('parser', {
        dataUrlCondition: () => false
      })
      .set('generator', {
        filename: 'img/[name].[hash:8][ext]',
        publicPath
      })
    // do not inline image assets
    config.module
      .rule('images')
      .set('parser', {
        dataUrlCondition: () => false
      })
      .set('generator', {
        filename: 'img/[name].[hash:8][ext]',
        publicPath
      })
    // do not inline media assets
    config.module.rule('media').set('parser', {
      dataUrlCondition: () => false
    })
    // do not inline font assets
    config.module.rule('fonts').set('parser', {
      dataUrlCondition: () => false
    })
  },
  configureWebpack: (config) => {
    if (process.env.NODE_ENV !== 'production') {
      config.devtool = 'eval-cheap-module-source-map'
    }

    config.output.filename =
      process.env.NODE_ENV === 'production'
        ? '[name].[contenthash:8].js'
        : 'js/[name].js'
    config.output.chunkFilename =
      process.env.NODE_ENV === 'production'
        ? '[name].[contenthash:8].js'
        : 'js/[name].js'
    config.externals = [
      // externalize all modules in node_modules folder
      nodeExternals({
        additionalModuleDirs: [path.join(PROJECT_DIR, 'node_modules')]
      })
    ]

    config.resolve.fallback = {
      buffer: require.resolve('buffer/'),
      http: require.resolve('stream-http'),
      https: require.resolve('https-browserify'),
      path: require.resolve('path-browserify'),
      url: require.resolve('url/')
    }

    config.plugins.push(
      new CopyWebpackPlugin({
        patterns: [
          // copy styles to output
          {
            from: path.join(__dirname, 'src/sass'),
            to: path.join(__dirname, 'dist/sass'),
            noErrorOnMissing: true
          },
          // copy assets (sources) to output
          {
            from: path.join(__dirname, 'src/assets'),
            to: path.join(__dirname, 'dist/assets'),
            noErrorOnMissing: true
          }
        ]
      })
    )
    config.plugins.push(new VuetifyLoaderPlugin())
  }
})
