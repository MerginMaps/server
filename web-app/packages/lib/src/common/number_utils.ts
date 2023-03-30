// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

const SizeUnits = {
  GB: (value: number) => (value / 1073741824).toFixed(2),
  MB: (value: number) => (value / 1048576).toFixed(2),
  kB: (value: number) => (value / 1024).toFixed(0),
  B: (value: number) => `${Math.round(value)}`
}

export function formatFileSize(
  value,
  unit?: keyof typeof SizeUnits,
  digits = 2,
  minUnit: keyof typeof SizeUnits = 'B'
) {
  if (!value) {
    return `${value} MB`
  }
  if (!unit) {
    if (value >= 1073741824 || minUnit === 'GB') {
      unit = 'GB'
    } else if (value >= 1048576 || minUnit === 'MB') {
      unit = 'MB'
    } else if (value >= 1024 || minUnit === 'kB') {
      unit = 'kB'
    } else {
      unit = 'B'
    }
  }
  let unitsValue = parseFloat(SizeUnits[unit](value))
  unitsValue = unitsValue === 0 ? Math.pow(10, -digits) : unitsValue
  return `${unitsValue.toFixed(digits)} ${unit}`
}

export function formatToCurrency(value: number, currency: string): string {
  return value.toLocaleString('en-UK', {
    style: 'currency',
    currency: currency,
    currencySign: 'accounting'
  })
}
