const CopyWebpackPlugin = require('copy-webpack-plugin')
const dotenv = require('dotenv')
const dotenvExpand = require('dotenv-expand')
const path = require('path')
const { VuetifyLoaderPlugin } = require('vuetify-loader')
const webpack = require('webpack')

const OUTPUT_DIR = 'dist'
const PROJECT_DIR = '../..'
const myEnv = dotenv.config({ path: path.join(PROJECT_DIR, '.env') })
dotenvExpand(myEnv)

const publicPath =
  process.env.NODE_ENV === 'production' && process.env.PUBLIC_PATH
    ? process.env.PUBLIC_PATH ?? '/'
    : '/'

const serverPort = process.env.FLASK_RUN_PORT ?? 5000

module.exports = {
  outputDir: OUTPUT_DIR,
  publicPath,
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

    config.devtool = 'source-map'
    config.output.filename =
      process.env.NODE_ENV === 'production'
        ? '[name].[contenthash:8].js'
        : 'js/[name].js'
    config.output.chunkFilename =
      process.env.NODE_ENV === 'production'
        ? '[name].[contenthash:8].js'
        : 'js/[name].js'

    // to enable switch in development server
    if (process.env.NODE_ENV !== 'production') {
      config.entry = './src/main.js'
    }

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
          // copy images from libraries
          {
            from: path.join(
              path.dirname(require.resolve(`@mergin/lib/package.json`)),
              'dist',
              'img'
            ),
            to: path.join(__dirname, OUTPUT_DIR, 'img'),
            noErrorOnMissing: true
          }
        ]
      })
    )
    config.plugins.push(
      new webpack.ProvidePlugin({
        process: 'process/browser'
      })
    )
    config.plugins.push(new VuetifyLoaderPlugin())
  },
  devServer: {
    static: {
      publicPath
    },
    proxy: {
      '/v1': {
        target: `http://localhost:${serverPort}`
      },
      '/app': {
        target: `http://localhost:${serverPort}`
      },
      '/ping': {
        target: `http://localhost:${serverPort}`
      },
      '/config': {
        target: `http://localhost:${serverPort}`
      }
    }
  },
  pluginOptions: {
    i18n: {
      locale: 'en',
      fallbackLocale: 'en',
      localeDir: 'locales',
      enableInSFC: false
    }
  }
}
