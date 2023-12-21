// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { RouteRecord } from 'vue-router'

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

export default (): RouteRecord[] => []
