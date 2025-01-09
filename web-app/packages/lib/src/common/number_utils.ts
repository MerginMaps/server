// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

export type SizeUnit = 'GB' | 'MB' | 'kB' | 'B'

const SizeUnits: Record<SizeUnit, (value: number) => string> = {
  GB: (value) => (value / 1073741824).toFixed(2),
  MB: (value) => (value / 1048576).toFixed(2),
  kB: (value) => (value / 1024).toFixed(0),
  B: (value) => `${Math.round(value)}`
}

export function formatFileSize(
  value,
  unit?: SizeUnit,
  digits = 2,
  minUnit: SizeUnit = 'B'
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

export function formatToCurrency(
  value: number,
  currency: string,
  digits = 2
): string {
  return value.toLocaleString('en-UK', {
    style: 'currency',
    currency,
    currencySign: 'accounting',
    maximumFractionDigits: digits
  })
}
