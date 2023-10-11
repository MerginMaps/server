// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import Vue from 'vue'
import VueI18n from 'vue-i18n'
import en from 'vuetify/lib/locale/en'

import enMessages from './locale/en.json'

Vue.use(VueI18n)

const messages = {
  en: {
    ...enMessages,
    $vuetify: en
  }
}

export default new VueI18n({
  locale: import.meta.env.VITE_VUE_APP_I18N_LOCALE || 'en',
  fallbackLocale: import.meta.env.VUE_APP_I18N_FALLBACK_LOCALE || 'en',
  messages
})
