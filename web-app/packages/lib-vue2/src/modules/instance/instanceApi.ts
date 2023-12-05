// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { AxiosResponse } from 'axios'

import { InstanceModule } from '@/modules/instance/module'
import {
  ConfigResponse,
  InitResponse,
  PingResponse
} from '@/modules/instance/types'

export const InstanceApi = {
  getInit: (): Promise<AxiosResponse<InitResponse>> => {
    return InstanceModule.httpService.get('/app/init')
  },
  getPing: (): Promise<AxiosResponse<PingResponse>> => {
    return InstanceModule.httpService.get('/ping')
  },
  getConfig: (): Promise<AxiosResponse<ConfigResponse>> => {
    return InstanceModule.httpService.get('/config')
  }
}
