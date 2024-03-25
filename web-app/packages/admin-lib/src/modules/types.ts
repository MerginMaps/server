// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { RootState as CeLibRootState } from '@mergin/lib-vue2'

import { AdminState } from '@/modules/admin'

export interface CeAdminLibRootState extends CeLibRootState {
  adminModule: AdminState
}
