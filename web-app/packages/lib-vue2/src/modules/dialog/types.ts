// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

// import Vue, { Component } from 'vue'

export interface DialogParams {
  dialog: Record<string, unknown>
  // TODO: clear unknown based on 'on-listener' in template
  listeners?: unknown | Record<string, (...args: unknown[]) => void>
  props?: Record<string, unknown>
}

export interface DialogPayload {
  params: DialogParams
  component: any
}
