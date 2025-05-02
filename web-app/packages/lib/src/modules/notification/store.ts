// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { defineStore } from 'pinia'
import { ToastServiceMethods } from 'primevue/toastservice'

import {
  NotificationPayload,
  NotificationShowPayload,
  NotificationState
} from './types'

/**
 * Defines a Pinia store for managing notifications.
 * In future - it should be possible to remove this store and use this.$toast or useToast in all components.
 *
 * The store exposes state for the current toast notification,
 * showing/adding new notifications, warning, error,
 * and displaying results.
 */
export const useNotificationStore = defineStore('notificationModule', {
  state: (): NotificationState => ({
    toast: null
  }),

  actions: {
    init(toast: ToastServiceMethods) {
      this.toast = toast
    },
    show(payload: NotificationShowPayload) {
      this.toast?.add({
        severity: payload.severity ?? 'success',
        summary: payload.text,
        detail: payload.detail,
        life: payload.sticky ? undefined : payload.life ?? 3000,
        group: payload.group
      })
    },
    warn(payload: NotificationPayload) {
      this.show({
        severity: 'warn',
        ...payload
      })
    },
    error(payload: NotificationPayload) {
      this.show({
        severity: 'error',
        ...payload
      })
    },
    displayResult(payload) {
      if (payload?.result?.success) {
        this.show({ text: payload?.result?.message })
      } else {
        this.error({
          text: payload?.result?.message,
          life: 5000
        })
      }
    },
    closeNotification() {
      this.toast.removeAllGroups()
    }
  }
})
