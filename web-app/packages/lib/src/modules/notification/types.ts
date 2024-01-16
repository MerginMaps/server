// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { ToastMessageOptions } from 'primevue/toast'
import { ToastServiceMethods } from 'primevue/toastservice'

export interface NotificationState {
  toast: ToastServiceMethods
}

export interface NotificationPayload {
  text: string
  detail?: string
  life?: number
}

export type NotificationShowPayload = NotificationPayload & {
  severity?: ToastMessageOptions['severity']
}
