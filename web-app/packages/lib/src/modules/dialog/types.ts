// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { Component } from 'vue'

import { TipMessageProps } from '@/common'

export interface ConfirmDialogProps {
  text: string
  severity?: 'primary' | 'danger' | 'warning'
  confirmText?: string
  cancelText?: string
  description?: string
  hint?: string
  confirmField?: { label: string; expected: string; placeholder?: string }
  /** Props to show a tip message under confirm input */
  message?: TipMessageProps & { title: string; description: string }
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
