// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { Component } from 'vue'

export interface DialogParams {
  dialog: {
    maxWidth?: number
    persistent?: boolean
    keepAlive?: boolean
    header: string
  }
  // TODO: clear unknown based on 'on-listener' in template
  listeners?: unknown | Record<string, (...args: unknown[]) => void>
  props?: Record<string, unknown>
}

export interface DialogPayload {
  params: DialogParams
  component: Component
}
