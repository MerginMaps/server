// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { AxiosResponse } from 'axios'

export class CustomError extends Error {
  response: AxiosResponse
  constructor(message: string, response) {
    super(message)
    Object.setPrototypeOf(this, CustomError.prototype)
    this.response = response
  }
}
