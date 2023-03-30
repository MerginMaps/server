// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import store, { NotificationState } from './store'
import { Module } from '@/common/types'
import { RootState } from '@/modules/types'

export const NotificationModule: Module<NotificationState, RootState> = {
  name: 'notificationModule',
  moduleStore: store,
  init: (_services) => {
    // none initialization required
  }
}
