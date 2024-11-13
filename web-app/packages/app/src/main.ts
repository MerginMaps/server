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
  useInstanceStore,
  initCsrfToken
} from '@mergin/lib'

import 'primevue/resources/primevue.min.css'
import 'primeflex/primeflex.min.css'
import '@mergin/lib/dist/sass/themes/mm-theme-light/theme.scss'
import '@tabler/icons-webfont/tabler-icons.min.css'
import '@mergin/lib/dist/style.css'

import { createMerginApp } from './app'
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

  // App initialization
  const instanceStore = useInstanceStore(pinia)
  const response = await instanceStore.initApp()
  initCsrfToken(response)
  createMerginApp().mount('#app')
}

main()
