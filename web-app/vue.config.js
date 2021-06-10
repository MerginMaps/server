const main = process.env.MAIN_FILE || 'main'

module.exports = {
  outputDir: '../server/build/static',
  publicPath: process.env.NODE_ENV === 'production' ? '/assets/' : '/',
  pages: process.env.NODE_ENV === 'production'
    ? {
      index: {
        entry: `src/${main}.js`,
        template: `public/index_${main}.html`,
        filename: '../../src/templates/app.html'
      }
    }
    : undefined,
  configureWebpack: config => {
    // to enable swich in development server
    if (process.env.NODE_ENV !== 'production') {
      config.entry = `./src/${main}.js`
    }
  },
  devServer: {
    proxy: {
      '/dev/init': {
        target: 'http://localhost:5000'
      },
      '/v1': {
        target: 'http://localhost:5000'
      },
      '/app': {
        target: 'http://localhost:5000'
      },
      '/auth': {
        target: 'http://localhost:5000'
      },
      '/ping': {
        target: 'http://localhost:5000'
      },
      '/orgs': {
        target: 'http://localhost:5000'
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
