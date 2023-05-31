// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { Component } from 'vue'

export interface DialogParamsPayload {
  dialog: Record<string, unknown>
  // TODO: clear unknown based on 'on-listener' in template
  listeners?: unknown | Record<string, (...args: unknown[]) => void>
  props?: Record<string, unknown>
}

export interface DialogParams extends DialogParamsPayload {
  component: Component
}
