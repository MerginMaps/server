// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { useNotificationStore } from '@/modules/notification'

const useCopyToClipboard = () => {
  const notificationStore = useNotificationStore()

  const copy = async (
    value: string | number | null | undefined,
    label = 'Value'
  ) => {
    if (value === null || value === undefined || value === '') {
      return
    }
    try {
      await navigator.clipboard.writeText(String(value))
      notificationStore.show({ text: `${label} copied to clipboard` })
    } catch {
      notificationStore.error({
        text: `Failed to copy ${label.toLowerCase()} to clipboard`
      })
    }
  }

  return { copy }
}

export default useCopyToClipboard
