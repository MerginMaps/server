module.exports = {
  content: ['./dist/**/*.{html,js}'],
  css: ['./dist/**/index-*.css'],
  output: './dist/assets/',
  extractors: [
    {
      extractor: (content) => content.match(/[A-z0-9-:/]+/g) || [],
      extensions: ['js']
    }
  ]
}
