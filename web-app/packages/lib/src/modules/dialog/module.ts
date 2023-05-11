// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

// import store, { DialogState } from './store'
import { Module } from '@/common/types'
import { RootState } from '@/modules/types'

export const DialogModule: Module<any, RootState> = {
  name: 'dialogModule',
  moduleStore: undefined,
  init: (_services) => {
    // none initialization required
  }
}
