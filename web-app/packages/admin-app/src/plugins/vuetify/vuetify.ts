// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { useI18n } from 'vue-i18n'
import { createVuetify } from 'vuetify'
import { createVueI18nAdapter } from 'vuetify/locale/adapters/vue-i18n'

import i18n from '@/plugins/i18n/i18n'
// import '@/sass/overrides.sass'

const colors = {
  primary: '#2d052d',
  secondary: '#00a884',
  accent: '#9C27b0',
  info: '#00CAE3',
  orange: '#F9AE00',
  inputColor: '#2d052d'
}

export default createVuetify({
  locale: {
    adapter: createVueI18nAdapter({ i18n, useI18n })
  },
  theme: {
    themes: {
      dark: { colors },
      light: { colors }
    }
  }
})
