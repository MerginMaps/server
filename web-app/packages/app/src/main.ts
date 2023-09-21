// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import {
  DialogModule,
  FormModule,
  UserModule,
  NotificationModule,
  moduleUtils,
  getHttpService,
  ProjectModule,
  LayoutModule,
  InstanceModule,
  useAppStore,
} from '@mergin/lib'

import { createMerginApp } from './app'
import { createRouter } from './router'
import { createPiniaInstance } from './store'

async function main() {
  createPiniaInstance()
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

  createMerginApp().$mount('#app')
  const router = createRouter()

  router.onError((e) => {
    const appStore = useAppStore()
    appStore.setServerError(e.message)
  })
}

main()
