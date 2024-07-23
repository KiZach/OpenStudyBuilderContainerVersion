module.exports = {
  root: true,
  env: {
    node: true,
  },
  extends: ['plugin:vue/vue3-recommended', 'eslint:recommended', 'prettier'],
  rules: {
    'vue/no-v-html': 'off',
    'vue/component-name-in-template-casing': [
      'error',
      'PascalCase',
      {
        registeredComponentsOnly: true,
        ignores: [],
      },
    ],
    'require-atomic-updates': 'off',
  },
}
