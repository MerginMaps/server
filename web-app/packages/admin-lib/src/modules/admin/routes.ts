// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { RouteLocationNormalizedLoaded, RouteRecord } from 'vue-router'

import { AdminRouteParams } from './types'

import returnTranslation from '@/../../lang/translate'

const t = (key: string) => returnTranslation(import.meta.env.VITE_LANG, key)

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
    [AdminRoutes.Login]: [t('SignIn'), t('MerginMapsAdminPanel')],
    [AdminRoutes.ACCOUNTS]: t('Accounts'),
    [AdminRoutes.ACCOUNT]: t('AccountDetails'),
    [AdminRoutes.OVERVIEW]: t('Overview'),
    [AdminRoutes.PROJECTS]: t('Projects'),
    [AdminRoutes.PROJECT]: [t('ProjectDetails'), params.projectName],
    [AdminRoutes.SETTINGS]: t('Settings'),
    [AdminRoutes.ProjectTree]: [t('Files'), params.projectName],
    [AdminRoutes.ProjectHistory]: [t('History'), params.projectName],
    [AdminRoutes.ProjectSettings]: [t('Settings'), params.projectName],
    [AdminRoutes.ProjectVersion]: [params.version_id, params.projectName],
    [AdminRoutes.FileVersionDetail]: [params.path, params.version_id]
  }
  return titles[route.name as AdminRoutes]
}

export const getRoutes = (): RouteRecord[] => []
