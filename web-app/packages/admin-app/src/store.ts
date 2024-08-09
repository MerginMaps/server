// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { createPinia, Pinia } from 'pinia'
import { markRaw } from 'vue'

let piniaInstance: Pinia | null = null

export const addRouterToPinia = (router) => {
  const piniaInstance = getPiniaInstance()
  piniaInstance.use(({ pinia }) => {
    pinia.router = markRaw(router)
  })
}

export const createPiniaInstance = () => {
  piniaInstance = createPinia()
}

export const getPiniaInstance = (): Pinia => {
  return piniaInstance
}
