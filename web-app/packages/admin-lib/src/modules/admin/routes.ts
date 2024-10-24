// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { RouteRecord } from 'vue-router'

export enum AdminRoutes {
  ACCOUNTS = 'accounts',
  ACCOUNT = 'account',
  PROJECTS = 'projects',
  PROJECT = 'project',
  SETTINGS = 'settings',
  ProjectTree = 'project-tree',
  ProjectHistory = 'project-versions',
  ProjectSettings = 'project-settings'
}

export const getRoutes = (): RouteRecord[] => []
