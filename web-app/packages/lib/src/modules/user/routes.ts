// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { RouteLocationNormalizedLoaded, RouteRecord } from 'vue-router'

import { UserRouteParams } from './types'

import returnTranslation from '@/../../lang/translate'
import { DEFAULT_PAGE_TITLE } from '@/common/route_utils'

const t = (key: string) => returnTranslation(import.meta.env.VITE_LANG, key)

/**
 * Enum for user routes names
 * Feel free to use it in application router as name attribute and in redirects from lib or app
 */
export enum UserRouteName {
  Login = 'login',
  ConfirmEmail = 'confirm_email',
  ChangePassword = 'change_password',
  UserProfile = 'user_profile'
}

export const getUserTitle = (route: RouteLocationNormalizedLoaded) => {
  const name = route.name as UserRouteName
  const params = route.params as UserRouteParams
  const titles: Record<UserRouteName, string | string[]> = {
    [UserRouteName.Login]: [
      params.reset ? t('ResetPassword') : t('SignIn'),
      DEFAULT_PAGE_TITLE
    ],
    [UserRouteName.ConfirmEmail]: [t('EmailConfirmation'), DEFAULT_PAGE_TITLE],
    [UserRouteName.ChangePassword]: [t('ChangePassword'), DEFAULT_PAGE_TITLE],
    [UserRouteName.UserProfile]: [t('YourProfile')]
  }
  return titles[name]
}

export default (): RouteRecord[] => []
