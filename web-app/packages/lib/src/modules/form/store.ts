// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import axios from 'axios'
import { defineStore } from 'pinia'

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
      this.errors[payload.componentId] = payload.errors
    },
    resetFormErrors(payload: MerginComponentUuidPayload) {
      delete this.errors[payload.componentId]
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
      let errorMessage =
        (payload?.error as string) ?? payload.generalMessage ?? 'Error'
      const notificationStore = useNotificationStore()
      if (!axios.isAxiosError(payload.error)) {
        await notificationStore.error({ text: errorMessage })
        return
      }

      if (
        axios.isAxiosError(payload.error) &&
        typeof payload.error?.response?.data === 'object'
      ) {
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
          return
        }
      } else {
        errorMessage = payload?.error?.response?.data ?? errorMessage
      }
      if (errorMessage) {
        // show error message in notification component
        await notificationStore.error({ text: errorMessage })
      }
    }
  }
})
