// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { AxiosError } from 'axios'

export type MerginComponentUuid = number
export type FormInputError = string
export type FormErrors = Record<string, FormInputError[]>
export type FormErrorMessage = string | undefined
export type FormErrorsData =
  | FormErrorMessage
  | FormErrors
  | { status: number; detail: FormErrorMessage }

export interface MerginComponentUuidPayload {
  componentId: MerginComponentUuid
}
export interface SetFormErrorPayload extends MerginComponentUuidPayload {
  errors: FormErrors
}

export interface ClearErrorsPayload extends MerginComponentUuidPayload {
  keepNotification?: boolean
}

export interface HandleErrorPayload extends MerginComponentUuidPayload {
  error: AxiosError<FormErrorsData>
  generalMessage: FormErrorMessage
}
