// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { defineStore } from 'pinia'
import { Component, markRaw } from 'vue'

import { DialogParams, DialogPayload } from './types'

export interface DialogState {
  isDialogOpen: boolean
  params: DialogParams
  component: Component
}

export const useDialogStore = defineStore('dialogModule', {
  state: (): DialogState => ({
    isDialogOpen: false,
    params: {
      dialog: {
        maxWidth: 500,
        header: 'Action'
      }
    },
    component: null
  }),

  getters: {
    dialogProps(state): DialogParams['dialog'] {
      return state.params
        ? state.params.dialog
        : { header: 'Action', maxWidth: 500 }
    }
  },

  actions: {
    openDialog(payload: DialogPayload) {
      this.isDialogOpen = true
      this.params = { ...payload.params }
      this.component = markRaw(payload.component)
    },
    closeDialog() {
      this.isDialogOpen = false
      this.component = null
    },
    changeParams(payload: { params: DialogParams }) {
      this.params = payload.params
    },
    show(payload: DialogPayload) {
      this.openDialog({
        params: { ...payload.params },
        component: payload.component
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
