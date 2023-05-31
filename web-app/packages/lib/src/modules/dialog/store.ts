// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { defineStore } from 'pinia'
import { Component } from 'vue'

import { DialogParams, DialogParamsPayload } from './types'

export interface DialogState {
  isDialogOpen: boolean
  params: DialogParams
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
    openDialog(payload: { params: DialogParams }) {
      this.isDialogOpen = true
      this.params = { ...payload.params }
    },
    closeDialog() {
      this.isDialogOpen = false
    },
    changeParams(payload: { params: DialogParams }) {
      this.params = payload.params
    },
    show(payload: { params: DialogParamsPayload; component: Component }) {
      this.openDialog({
        params: { ...payload.params, component: payload.component }
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
