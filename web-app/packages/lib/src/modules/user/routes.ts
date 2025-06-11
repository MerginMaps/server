// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { RouteLocationNormalizedLoaded, RouteRecord } from 'vue-router'

import { UserRouteParams } from './types'

import { DEFAULT_PAGE_TITLE } from '@/common/route_utils'

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
      params.reset ? 'Reset password' : 'Sign in',
      DEFAULT_PAGE_TITLE
    ],
    [UserRouteName.ConfirmEmail]: ['Confirm email address', DEFAULT_PAGE_TITLE],
    [UserRouteName.ChangePassword]: ['Change password', DEFAULT_PAGE_TITLE],
    [UserRouteName.UserProfile]: ['Your profile']
  }
  return titles[name]
}

export default (): RouteRecord[] => []
