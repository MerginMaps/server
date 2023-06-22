// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import Vue from 'vue'
import Vuetify from 'vuetify/lib/framework'

import i18n from '@/plugins/i18n/i18n'
// import '@/sass/overrides.sass'

Vue.use(Vuetify)

const theme = {
  primary: '#2d052d',
  secondary: '#00a884',
  accent: '#9C27b0',
  info: '#00CAE3',
  orange: '#F9AE00',
  inputColor: '#2d052d'
}

export default new Vuetify({
  lang: {
    t: (key, ...params) => i18n.t(key, params)
  },
  theme: {
    themes: {
      dark: theme,
      light: theme
    }
  }
})
