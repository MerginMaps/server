// Copyright (C) 2018 Lutra Consulting Limited. All rights reserved.
// Do not distribute without the express permission of the author.

import Path from 'path'
import diffInYears from 'date-fns/difference_in_years'
import diffInMonths from 'date-fns/difference_in_months'
import diffInWeeks from 'date-fns/difference_in_weeks'
import diffInDays from 'date-fns/difference_in_days'
import diffInHours from 'date-fns/difference_in_hours'
import diffInMinutes from 'date-fns/difference_in_minutes'


export function dirname (path) {
  const dir = Path.dirname(path).replace(/\/$/, '')
  return dir === '.' ? '' : dir
}

export function removeAccents (text) {
  return text.normalize('NFD').replace(/[\u0300-\u036f]/g, '')
}

const SizeUnits = {
  GB: value => (value / 1073741824).toFixed(2),
  MB: value => (value / 1048576).toFixed(2),
  kB: value => (value / 1024).toFixed(0),
  B: value => Math.round(value)
}

export function formatFileSize (value, unit, digits = 2, minUnit = 'B') {
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

export function formatDateTime (isoString) {
  return isoString ? new Date(isoString).toUTCString() : ''
}

export function formatDate (isoString) {
  return isoString ? new Date(isoString).toDateString() : ''
}

const DurationKeys = {
  years: ['year', 'years'],
  months: ['month', 'months'],
  weeks: ['week', 'weeks'],
  days: ['day', 'days'],
  hours: ['hour', 'hours'],
  minutes: ['minute', 'minutes']
}

function formatDuration (num, unit) {
  return `${num} ${DurationKeys[unit][num === 1 ? 0 : 1]} ago`
}

function remainingFormatDuration (num, unit) {
  return `${num} ${DurationKeys[unit][num === 1 ? 0 : 1]}`
}

export function formatTimeDiff (t1, t2 = new Date()) {
  if (!t1) {
    return '-'
  }
  const days = diffInDays(t2, t1)
  if (days > 365) {
    return formatDuration(diffInYears(t2, t1), 'years')
  }
  if (days > 31) {
    return formatDuration(diffInMonths(t2, t1), 'months')
  }
  if (days > 6) {
    return formatDuration(diffInWeeks(t2, t1), 'weeks')
  }
  if (days < 1) {
    const hours = diffInHours(t2, t1)
    if (hours < 1) {
      const minutes = diffInMinutes(t2, t1)
      if (minutes < 0) {
        return 'N/A'
      }
      return formatDuration(minutes, 'minutes')
    }
    return formatDuration(hours, 'hours')
  }
  return formatDuration(days, 'days')
}

export function formatRemainingTime (t2, t1 = new Date()) {
  if (!t1) {
    return '-'
  }
  const days = diffInDays(t2, t1)
  const hours = diffInHours(t2, t1)
  switch (true) {
    case (days > 365):
      return remainingFormatDuration(diffInYears(t2, t1), 'years')
    case (days > 31):
      return remainingFormatDuration(diffInMonths(t2, t1), 'months')
    case (days > 6):
      return remainingFormatDuration(diffInWeeks(t2, t1), 'weeks')
    case (days < 1):
      if (days < 0) { return 'expired' }
      if (hours < 1) {
        const minutes = diffInMinutes(t2, t1)
        return remainingFormatDuration(minutes, 'minutes')
      }
      return remainingFormatDuration(hours, 'hours')
    default:
      return remainingFormatDuration(days, 'days')
  }
}

export function waitCursor (on) {
  document.body.style.cursor = (on) ? 'wait' : 'default'
}

export function downloadJsonList (jsonList, headers, filename, output = 'csv') {
  /** download json as csv, but we need to put it in one level
   :param jsonList: dict **/
  if (!jsonList || !headers) {
    return
  }
  headers = headers.filter(h => h.value)
  const headerTexts = Object.keys(headers).map(function (key) {
    return headers[key].text
  })
  const headerValues = Object.keys(headers).map(function (key) {
    return headers[key].value
  })
  if (output === 'csv') {
    let content = headerTexts.join(';') + '\n'
    jsonList.forEach(function (row) {
      let currentContent = ''
      headerValues.forEach(function (header) {
        const headerSplit = header.split('.')
        if (headerSplit.length > 1) {
          currentContent += (row[headerSplit[0]][headerSplit[1]] !== null ? row[headerSplit[0]][headerSplit[1]] : '') + ';'
        } else {
          currentContent += (row[header] !== null ? row[header] : '') + ';'
        }
      })
      content += currentContent + '\n'
    })
    const hiddenElement = document.createElement('a')
    hiddenElement.href = 'data:text/csv;charset=utf-8,' + encodeURI(content)
    hiddenElement.target = '_blank'
    hiddenElement.download = filename + '.csv'
    hiddenElement.click()
    document.removeChild(hiddenElement)
  }
}

export function formatToTitle (string) {
  string = string.replace(/_/g, ' ')
  return string.charAt(0).toUpperCase() + string.slice(1)
}

export function formatToCurrency (value, currency) {
  return value.toLocaleString('en-UK', {
    style: 'currency',
    currency: currency,
    currencySign: 'accounting'
  })
}

export class CustomError extends Error {
  constructor (message, response) {
    super(message)
    this.response = response
  }
}
