module.exports = {
  root: true,
  env: {
    es2021: true
  },
  extends: [
    'plugin:vue/essential',
    '@vue/standard',
    'plugin:prettier/recommended'
  ],
  plugins: ['@typescript-eslint'],
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
    ],
    // Vue 3 opt https://v3-migration.vuejs.org/breaking-changes/key-attribute.html#with-template-v-for
    'vue/no-v-for-template-key-on-child': 'error',
    'vue/no-v-for-template-key': 'off'
  }
}
