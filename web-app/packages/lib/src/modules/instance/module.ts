// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

// import store, { InstanceState } from './store'
import { Module } from '@/common/types'
import { RootState } from '@/modules/types'

export const InstanceModule: Module<any, RootState> = {
  name: 'instanceModule',
  httpService: undefined,
  moduleStore: undefined,
  init: (services) => {
    if (services.httpService) {
      InstanceModule.httpService = services.httpService
    } else {
      console.error(`Module ${InstanceModule.name} - missing httpService`)
    }
  }
}
