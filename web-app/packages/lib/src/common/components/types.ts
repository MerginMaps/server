// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

export interface DropdownOption<T = string> {
  value: T
  label: string
  description?: string
}
