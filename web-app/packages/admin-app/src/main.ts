// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { AdminModule } from '@mergin/admin-lib'
import {
  DialogModule,
  FormModule,
  getHttpService,
  InstanceModule,
  LayoutModule,
  moduleUtils,
  NotificationModule,
  ProjectModule,
  UserModule,
  useAppStore,
  useInstanceStore,
  initCsrfToken
} from '@mergin/lib'

import { createMerginApp } from './app'
import { createRouter } from './router'
import { createPiniaInstance, getPiniaInstance } from './store'

async function main() {
  createPiniaInstance()
  const pinia = getPiniaInstance()
  const httpService = getHttpService()
  // initialize modules
  moduleUtils.initializeAppModule(LayoutModule)
  moduleUtils.initializeAppModule(UserModule, {
    httpService
  })
  moduleUtils.initializeAppModule(NotificationModule)
  moduleUtils.initializeAppModule(DialogModule)
  moduleUtils.initializeAppModule(FormModule)
  moduleUtils.initializeAppModule(ProjectModule, {
    httpService
  })
  moduleUtils.initializeAppModule(InstanceModule, {
    httpService
  })
  moduleUtils.initializeAppModule(AdminModule, {
    httpService
  })
  // App initialization
  const instanceStore = useInstanceStore(pinia)
  const response = await instanceStore.initApp()
  initCsrfToken(response)
  const router = createRouter(pinia)
  createMerginApp().$mount('#app')

  router.onError((e) => {
    const appStore = useAppStore()
    appStore.setServerError(e.message)
  })
}

main()
