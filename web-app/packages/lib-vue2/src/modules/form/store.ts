// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { defineStore } from 'pinia'
import Vue from 'vue'

import {
  ClearErrorsPayload,
  FormErrors,
  HandleErrorPayload,
  MerginComponentUuid,
  MerginComponentUuidPayload,
  SetFormErrorPayload
} from '@/modules/form/types'
import { useNotificationStore } from '@/modules/notification/store'

export interface FormState {
  errors: Record<MerginComponentUuid, FormErrors>
}

export const useFormStore = defineStore('formModule', {
  state: (): FormState => ({
    errors: {}
  }),

  getters: {
    getErrorByComponentId: (state) => (payload: MerginComponentUuid) => {
      return state.errors[payload]
    }
  },

  actions: {
    setFormErrors(payload: SetFormErrorPayload) {
      Vue.set(this.errors, payload.componentId, payload.errors)
    },
    resetFormErrors(payload: MerginComponentUuidPayload) {
      Vue.delete(this.errors, payload.componentId)
    },
    clearErrors(payload: ClearErrorsPayload) {
      const notificationStore = useNotificationStore()
      this.resetFormErrors(payload)
      if (!payload.keepNotification) {
        // reset error message in notification component
        notificationStore.closeNotification()
      }
    },
    async handleError(payload: HandleErrorPayload) {
      let errorMessage
      const notificationStore = useNotificationStore()
      if (typeof payload.error?.response?.data === 'object') {
        // two types of error responses
        // TODO: Get data from HTTP status code, handle formError not standard error with detail
        if (
          typeof payload.error.response.data.status === 'number' ||
          payload.error.response.data.detail
        ) {
          errorMessage = payload.error.response.data.detail
        } else {
          this.setFormErrors({
            componentId: payload.componentId,
            errors: payload.error.response.data
          })
        }
      } else {
        errorMessage =
          payload?.error?.response?.data ??
          payload.generalMessage ??
          payload?.error ??
          'Error'
      }
      if (errorMessage) {
        // show error message in notification component
        await notificationStore.error({ text: errorMessage })
      }
    }
  }
})
