// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { AdminModule } from '@mergin/admin-lib'
import {
  DialogModule,
  FormModule,
  http,
  initCsrfToken,
  InstanceModule,
  LayoutModule,
  moduleUtils,
  NotificationModule,
  ProjectModule,
  UserModule
} from '@mergin/lib'

import { createMerginApp } from './app'
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
moduleUtils.initializeAppModule(AdminModule, {
  httpService: http,
  routerService: router,
  store
})

// App initialization
store.dispatch('instanceModule/initApp').then(async (response) => {
  initCsrfToken(response)
  await store.dispatch('instanceModule/fetchConfig')
  createMerginApp().mount('#app')
})
