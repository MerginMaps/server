// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import Path from 'path'

export function dirname(path: string) {
  const dir = Path.dirname(path).replace(/\/$/, '')
  return dir === '.' ? '' : dir
}
