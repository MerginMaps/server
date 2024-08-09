// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { createI18n } from 'vue-i18n'

export default createI18n({
  legacy: false, // Vuetify does not support the legacy mode of vue-i18n
  locale: import.meta.env.VITE_VUE_APP_I18N_LOCALE || 'en',
  allowComposition: true,
  fallbackLocale: import.meta.env.VITE_VUE_APP_I18N_FALLBACK_LOCALE || 'en'
})
