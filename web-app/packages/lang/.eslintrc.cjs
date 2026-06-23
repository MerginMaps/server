module.exports = {
  root: true,
  ignorePatterns: ['*.d.ts'],
  extends: ['../../.eslintrc.cjs'],
  parser: '@typescript-eslint/parser',
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module'
  },
  plugins: ['@typescript-eslint'],
  overrides: [
    {
      files: ['translations/*.ts'],
      rules: {
        'prettier/prettier': 'off'
      }
    }
  ]
}
