// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { Component } from 'vue'

export interface ConfirmDialogProps {
  text: string
  severity?: 'primary' | 'danger'
  confirmText?: string
  cancelText?: string
  description?: string
  hint?: string
  confirmField?: { label: string; expected: string }
}

export interface DialogParams {
  dialog: {
    maxWidth?: number
    persistent?: boolean
    keepAlive?: boolean
    header: string
  }
  // TODO: clear unknown based on 'on-listener' in template
  listeners?: unknown | Record<string, (...args: unknown[]) => void>
  props?: object | ConfirmDialogProps
}

export interface DialogPayload {
  params: DialogParams
  component: Component
}
