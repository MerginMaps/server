// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

export class CustomError extends Error {
  response: any
  constructor(message: string, response) {
    super(message)
    Object.setPrototypeOf(this, CustomError.prototype)
    this.response = response
  }
}
