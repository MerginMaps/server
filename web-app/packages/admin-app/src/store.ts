// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { createPinia, Pinia, PiniaVuePlugin } from 'pinia'
import Vue from 'vue'

Vue.use(PiniaVuePlugin)

let piniaInstance: Pinia | null = null

export const addRouterToPinia = (router) => {
  const piniaInstance = getPiniaInstance()
  piniaInstance.router = router
}

export const createPiniaInstance = () => {
  piniaInstance = createPinia()
}

export const getPiniaInstance = (): Pinia => {
  return piniaInstance
}
