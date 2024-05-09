// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { getAvatar } from './mergin_utils'

import {
  formatDate,
  formatDateTime,
  formatRemainingTime,
  formatTimeDiff
} from '@/common/date_utils'
import { formatFileSize, formatToCurrency } from '@/common/number_utils'
import { formatToTitle } from '@/common/text_utils'

export * from './components'
export * from './errors'
export * from './mixins'
export * from './http'
export * from './types'
// export * from './router_without_navigation_failure'
export * as dateUtils from './date_utils'
export * as htmlUtils from './html_utils'
export * as merginUtils from './mergin_utils'
export * as moduleUtils from './module_utils'
export * as numberUtils from './number_utils'
export * as pathUtils from './path_utils'
export * as permissionUtils from './permission_utils'
export * as textUtils from './text_utils'
export * as routeUtils from './route_utils'
export * as errorUtils from './error_utils'

export interface ComponentCustomPropertyFilters {
  filesize: typeof formatFileSize
  datetime: typeof formatDateTime
  date: typeof formatDate
  timediff: typeof formatTimeDiff
  remainingtime: typeof formatRemainingTime
  totitle: typeof formatToTitle
  currency: typeof formatToCurrency
  getAvatar: typeof getAvatar
}
