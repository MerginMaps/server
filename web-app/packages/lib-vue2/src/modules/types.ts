// Copyright (C) 2022 Lutra Consulting Limited. All rights reserved.
// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { DialogState } from '@/modules/dialog'
import { FormState } from '@/modules/form'
import { InstanceState } from '@/modules/instance'
import { LayoutState } from '@/modules/layout'
import { NotificationState } from '@/modules/notification'
import { ProjectState } from '@/modules/project'
import { UserState } from '@/modules/user'

export interface RootState {
  dialogModule: DialogState
  formModule: FormState
  instanceModule: InstanceState
  layoutModule: LayoutState
  notificationModule: NotificationState
  projectModule: ProjectState
  userModule: UserState
}
