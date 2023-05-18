// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { defineStore } from 'pinia'

export interface DialogState {
  isDialogOpen: boolean
  params: Record<string, any>
}

export const useDialogStore = defineStore('dialogModule', {
  state: (): DialogState => ({
    isDialogOpen: false,
    params: null
  }),

  getters: {
    dialogProps(state) {
      return state.params ? state.params.dialog : {}
    }
  },

  actions: {
    openDialog(payload) {
      this.isDialogOpen = true
      this.params = payload.params
    },
    closeDialog() {
      this.isDialogOpen = false
    },
    changeParams(payload) {
      this.params = payload.params
    },
    show(payload) {
      this.openDialog({
        params: { ...payload.params, component: payload.component }
      })
    },
    prompt(payload) {
      this.show({
        params: payload.params
      })
    },
    close() {
      this.closeDialog()
      if (this.params?.dialog && !this.params.dialog.keepAlive) {
        setTimeout(() => {
          this.changeParams({ params: null })
        }, 300)
      }
    }
  }
})
