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
  InstanceModule,
  useInstanceStore
} from '@mergin/lib'

import { createMerginApp } from './app'
import router from './router'
import { getPiniaInstance } from './store'

// initialize modules
moduleUtils.initializeAppModule(LayoutModule)
moduleUtils.initializeAppModule(UserModule, {
  httpService: http,
  routerService: router
})
moduleUtils.initializeAppModule(NotificationModule)
moduleUtils.initializeAppModule(DialogModule)
moduleUtils.initializeAppModule(FormModule)
moduleUtils.initializeAppModule(ProjectModule, {
  httpService: http,
  routerService: router
})
moduleUtils.initializeAppModule(InstanceModule, {
  httpService: http
})

const instanceStore = useInstanceStore(getPiniaInstance())
// App initialization
instanceStore.initApp().then(async (response) => {
  initCsrfToken(response)
  await instanceStore.fetchConfig()
  const app = createMerginApp()
  app.$mount('#app')
})
