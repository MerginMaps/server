// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

// styles must be imported first (at least before imports of our libs)
import 'vuetify/dist/vuetify.min.css'
import 'material-icons/iconfont/material-icons.scss'
import '@fortawesome/fontawesome-free/css/all.css'
import '@mdi/font/css/materialdesignicons.css'

import '@mergin/lib/dist/style.css'
import '@mergin/admin-lib/dist/style.css'

import {
  dateUtils,
  textUtils,
  numberUtils,
  http,
  MerginComponentUuidMixin,
  useAppStore
} from '@mergin/lib'
import PortalVue from 'portal-vue'
import { createApp } from 'vue'
// import VueMeta from 'vue-meta'

import App from './App.vue'
import router from './router'
import { getPiniaInstance } from './store'

import i18n from '@/plugins/i18n/i18n'
import vuetify from '@/plugins/vuetify/vuetify'

// TODO: V3_UPGRADE - https://github.com/nuxt/vue-meta/issues/665#issuecomment-820927172
// Vue.use(VueMeta)

const createMerginApp = () => {
  router.onError((e) => {
    const appStore = useAppStore()
    appStore.setServerError(e.message)
  })

  const app = createApp(App)
    // global mixin - replace with composable after migration to Vue 3
    .mixin(MerginComponentUuidMixin)
    .use(getPiniaInstance())
    .use(router)
    .use(vuetify)
    .use(i18n)
    .use(PortalVue)

  app.config.globalProperties.$http = http
  app.config.globalProperties.$filters = {
    filesize: (value, unit, digits = 2, minUnit: numberUtils.SizeUnit = 'B') =>
      numberUtils.formatFileSize(value, unit, digits, minUnit),
    datetime: dateUtils.formatDateTime,
    date: dateUtils.formatDate,
    timediff: dateUtils.formatTimeDiff,
    remainingtime: dateUtils.formatRemainingTime,
    totitle: textUtils.formatToTitle,
    currency: numberUtils.formatToCurrency
  }

  return app
}

export { createMerginApp }
