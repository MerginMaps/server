// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import axios from 'axios'

export function getErrorMessage(e: unknown, fallbackMessage?: string) {
  let text: string
  if (axios.isAxiosError(e)) {
    text = e.response.data?.detail ?? fallbackMessage
  } else if (fallbackMessage) {
    text = fallbackMessage
  } else if (e instanceof Error) {
    text = e.message
  }
  return text
}
