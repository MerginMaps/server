// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { createPinia, Pinia } from 'pinia'

let piniaInstance: Pinia | null = null

export const getPiniaInstance = (): Pinia => {
  if (piniaInstance !== null) {
    return piniaInstance
  }

  piniaInstance = createPinia()

  return piniaInstance
}
