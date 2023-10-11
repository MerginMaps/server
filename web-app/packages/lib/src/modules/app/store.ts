// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { defineStore } from 'pinia'

export interface AppState {
  serverError: string
}

export const useAppStore = defineStore('appModule', {
  state: (): AppState => ({
    serverError: null // TODO: global - check if used
  }),

  actions: {
    setServerError(msg) {
      this.serverError = msg
    }
  }
})
