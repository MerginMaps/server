// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import {
  dateUtils,
  textUtils,
  numberUtils,
  MerginComponentUuidMixin,
  MMTheme,
  merginUtils,
  useAppStore
} from '@mergin/lib'
import PrimeVue from 'primevue/config'
import Toast from 'primevue/toast'
import ToastService from 'primevue/toastservice'
import Tooltip from 'primevue/tooltip'
import { createApp } from 'vue'
import { createMetaManager } from 'vue-meta'

import App from './App.vue'
import { createRouter } from './router'
import { addRouterToPinia, getPiniaInstance } from './store'

const createMerginApp = () => {
  const pinia = getPiniaInstance()
  const router = createRouter(pinia)
  addRouterToPinia(router)
  router.onError((e) => {
    const appStore = useAppStore()
    appStore.setServerError(e.message)
  })

  const app = createApp(App)
    .mixin(MerginComponentUuidMixin)
    .use(pinia)
    .use(router)
    .use(createMetaManager())
    .use(PrimeVue, { pt: MMTheme })
    .use(ToastService)
    .component('PToast', Toast)
    .directive('tooltip', Tooltip)

  app.config.globalProperties.$filters = {
    filesize: (value, unit, digits = 2, minUnit: numberUtils.SizeUnit = 'B') =>
      numberUtils.formatFileSize(value, unit, digits, minUnit),
    datetime: dateUtils.formatDateTime,
    date: dateUtils.formatDate,
    timediff: dateUtils.formatTimeDiff,
    remainingtime: dateUtils.formatRemainingTime,
    totitle: textUtils.formatToTitle,
    currency: numberUtils.formatToCurrency,
    getAvatar: merginUtils.getAvatar
  }

  return app
}
export { createMerginApp }
