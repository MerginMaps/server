// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import {
  DialogModule,
  FormModule,
  UserModule,
  NotificationModule,
  moduleUtils,
  http,
  initCsrfToken,
  ProjectModule,
  LayoutModule,
  InstanceModule
} from '@mergin/lib'

import { createApp } from './app'
import router from './router'
import store from './store'

// initialize modules
moduleUtils.initializeAppModule(LayoutModule, {
  store
})
moduleUtils.initializeAppModule(UserModule, {
  httpService: http,
  routerService: router,
  store
})
moduleUtils.initializeAppModule(NotificationModule, {
  store
})
moduleUtils.initializeAppModule(DialogModule, {
  store
})
moduleUtils.initializeAppModule(FormModule, {
  store
})
moduleUtils.initializeAppModule(ProjectModule, {
  httpService: http,
  routerService: router,
  store
})
moduleUtils.initializeAppModule(InstanceModule, {
  httpService: http,
  store
})

// App initialization
store.dispatch('instanceModule/initApp').then(async (response) => {
  initCsrfToken(response)
  await store.dispatch('instanceModule/fetchConfig')
  createApp().$mount('#app')
})
