// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { Module } from '@/common/types'

export const InstanceModule: Module = {
  name: 'instanceModule',
  httpService: undefined,
  init: (services) => {
    if (services.httpService) {
      InstanceModule.httpService = services.httpService
    } else {
      console.error(`Module ${InstanceModule.name} - missing httpService`)
    }
  }
}
