// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

// import store, { LayoutState } from './store'
import { Module } from '@/common/types'
import { RootState } from '@/modules/types'

export const LayoutModule: Module<any, RootState> = {
  name: 'layoutModule',
  moduleStore: undefined,
  init: (_services) => {
    // none initialization required
  }
}
