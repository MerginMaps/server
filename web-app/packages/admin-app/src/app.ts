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
  getHttpService,
  MerginComponentUuidMixin
} from '@mergin/lib'
import PortalVue from 'portal-vue'
import Vue from 'vue'
import VueMeta from 'vue-meta'

import App from './App.vue'
import router from './router'
import { getPiniaInstance } from './store'

import i18n from '@/plugins/i18n/i18n'
import vuetify from '@/plugins/vuetify/vuetify'

Vue.config.productionTip = false
Vue.use(PortalVue)
Vue.use(VueMeta)
Vue.prototype.$http = getHttpService()

Vue.filter('filesize', (value, unit, digits = 2, minUnit = 'B') => {
  return numberUtils.formatFileSize(value, unit, digits, minUnit)
})
Vue.filter('datetime', dateUtils.formatDateTime)
Vue.filter('date', dateUtils.formatDate)
Vue.filter('timediff', dateUtils.formatTimeDiff)
Vue.filter('remainingtime', dateUtils.formatRemainingTime)
Vue.filter('totitle', textUtils.formatToTitle)
Vue.filter('currency', numberUtils.formatToCurrency)

// global mixin - replace with composable after migration to Vue 3
Vue.mixin(MerginComponentUuidMixin)

const createMerginApp = (): Vue => {
  const pinia = getPiniaInstance()

  return new Vue({
    router,
    pinia,
    vuetify,
    i18n,
    render: (h) => h(App)
  })
}

export { createMerginApp }
