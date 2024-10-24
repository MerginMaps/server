module.exports = {
  root: true,
  env: {
    es2022: true,
    browser: true,
    node: true
  },
  extends: ['plugin:vue/vue3-essential', 'plugin:prettier/recommended'],
  plugins: ['@typescript-eslint', 'eslint-plugin-import'],
  rules: {
    'prettier/prettier': 'warn',
    '@typescript-eslint/no-unused-vars': [
      'warn',
      {
        argsIgnorePattern: '^_',
        varsIgnorePattern: '^_',
        caughtErrorsIgnorePattern: '^_'
      }
    ],
    'import/order': [
      'warn',
      {
        groups: [
          ['builtin', 'external'],
          ['internal', 'parent', 'sibling'],
          ['index', 'object', 'type']
        ],
        'newlines-between': 'always',
        alphabetize: {
          order: 'asc',
          caseInsensitive: true
        }
      }
    ],
    'no-console': process.env.NODE_ENV === 'production' ? 'error' : 'off',
    'no-debugger': process.env.NODE_ENV === 'production' ? 'error' : 'off',
    'no-multiple-empty-lines': ['warn', { max: 2 }],
    'vue/valid-v-slot': [
      'error',
      {
        allowModifiers: true
      }
    ]
  }
}
