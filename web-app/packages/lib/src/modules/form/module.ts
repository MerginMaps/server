// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

// import store, { FormState } from './store'
import { Module } from '@/common/types'
import { RootState } from '@/modules/types'

export const FormModule: Module<any, RootState> = {
  name: 'formModule',
  moduleStore: undefined,
  init: (_services) => {
    // none initialization required
  }
}
