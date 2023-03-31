// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import store, { LayoutState } from './store'
import { Module } from '@/common/types'
import { RootState } from '@/modules/types'

export const LayoutModule: Module<LayoutState, RootState> = {
  name: 'layoutModule',
  moduleStore: store,
  init: (_services) => {
    // none initialization required
  }
}
