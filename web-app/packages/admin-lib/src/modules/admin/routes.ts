// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { RouteLocationNormalizedLoaded, RouteRecord } from 'vue-router'

import { AdminRouteParams } from './types'

export enum AdminRoutes {
  ACCOUNTS = 'accounts',
  ACCOUNT = 'account',
  OVERVIEW = 'overview',
  PROJECTS = 'projects',
  PROJECT = 'project',
  SETTINGS = 'settings',
  ProjectTree = 'project-tree',
  ProjectHistory = 'project-versions',
  ProjectSettings = 'project-settings',
  ProjectVersion = 'project-version',
  FileVersionDetail = 'file-version-detail',
  Login = 'login'
}

export const getAdminTitle = (route: RouteLocationNormalizedLoaded) => {
  const params = route.params as AdminRouteParams
  const titles: Record<AdminRoutes, string | string[]> = {
    [AdminRoutes.Login]: ['Sign in', 'Mergin Maps Admin Panel'],
    [AdminRoutes.ACCOUNTS]: 'Accounts',
    [AdminRoutes.ACCOUNT]: 'Account details',
    [AdminRoutes.OVERVIEW]: 'Admin overview',
    [AdminRoutes.PROJECTS]: 'Projects',
    [AdminRoutes.PROJECT]: ['Details', params.projectName],
    [AdminRoutes.SETTINGS]: 'Settings',
    [AdminRoutes.ProjectTree]: ['Files', params.projectName],
    [AdminRoutes.ProjectHistory]: ['History', params.projectName],
    [AdminRoutes.ProjectSettings]: ['Settings', params.projectName],
    [AdminRoutes.ProjectVersion]: [params.version_id, params.projectName],
    [AdminRoutes.FileVersionDetail]: [params.path, params.version_id]
  }
  return titles[route.name as AdminRoutes]
}

export const getRoutes = (): RouteRecord[] => []
