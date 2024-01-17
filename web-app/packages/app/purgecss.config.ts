module.exports = {
  content: ['./dist/**/*.{html,js}'],
  css: ['./dist/**/index-*.css'],
  output: './dist/assets/',
  safelist: [/^lg:col-([0-9]|10|11|12)/, /^col-([0-9]|10|11|12)/],
  extractors: [
    {
      extractor: (content) => content.match(/[A-z0-9-:/]+/g) || [],
      extensions: ['js']
    }
  ]
}
