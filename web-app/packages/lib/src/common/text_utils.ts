// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

export function formatToTitle(string: string) {
  string = string.replace(/_/g, ' ')
  return string.charAt(0).toUpperCase() + string.slice(1)
}

export function removeAccents(text: string) {
  return text.normalize('NFD').replace(/[\u0300-\u036f]/g, '')
}

export function isValidEmail(email: string) {
  const emailPattern =
    /^(([^<>()[\]\\.,;:\s@"]+(\.[^<>()[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/
  return emailPattern.test(email)
}

/**
 * The regular expression to split on. Splits a string into parts separated by whitespace or , and ;.
 */
export const EMAIL_LIST_SEPARATORS = /\s+|[,;]/
export const EMAIL_LIST_DEFAULT_SEPARATOR = ';'
