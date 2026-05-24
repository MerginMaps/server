// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

export interface DropdownOption<T = string> {
  value: T
  label: string
  description?: string
  disabled?: boolean
}

export interface TableDataHeader {
  header: string
  field: string
  sortable?: boolean
  width?: number
  linked?: boolean
  class?: string
  type?: 'boolean' | 'filesize' | 'timediff'
  conditionalLink?: string
}

export type TipMessageSeverity = 'info' | 'danger'

export interface TipMessageProps {
  severity?: TipMessageSeverity
}
