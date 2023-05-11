// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

// import store, { InstanceState } from './store'
import { Module } from '@/common/types'
import { RootState } from '@/modules/types'

export const AppModule: Module<any, RootState> = {
  name: 'instanceModule',
  moduleStore: undefined,
  init: (_services) => {
    // none initialization required
  }
}
