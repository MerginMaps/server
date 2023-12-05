module.exports = {
  env: {
    node: true
  },
  extends: [
    'plugin:vue/essential',
    'eslint:recommended',
    '@vue/typescript/recommended'
  ],
  parser: 'vue-eslint-parser',
  parserOptions: {
    parser: '@typescript-eslint/parser',
    ecmaVersion: 2020,
    sourceType: 'module'
  },
  plugins: ['@typescript-eslint'],
  rules: {
    'no-console': process.env.NODE_ENV === 'production' ? 'warn' : 'off',
    'no-debugger': process.env.NODE_ENV === 'production' ? 'warn' : 'off',
    // Vue 3 opt https://v3-migration.vuejs.org/breaking-changes/key-attribute.html#with-template-v-for
    'vue/no-v-for-template-key-on-child': 'error',
    'vue/no-v-for-template-key': 'off',
    'vue/no-multiple-template-root': 'off',
  }
}
