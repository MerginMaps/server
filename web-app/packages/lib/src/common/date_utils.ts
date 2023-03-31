// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import diffInDays from 'date-fns/differenceInDays'
import diffInHours from 'date-fns/differenceInHours'
import diffInMinutes from 'date-fns/differenceInMinutes'
import diffInMonths from 'date-fns/differenceInMonths'
import diffInWeeks from 'date-fns/differenceInWeeks'
import diffInYears from 'date-fns/differenceInYears'
import isDate from 'date-fns/isDate'
import isValid from 'date-fns/isValid'

const DurationKeys = {
  years: ['year', 'years'],
  months: ['month', 'months'],
  weeks: ['week', 'weeks'],
  days: ['day', 'days'],
  hours: ['hour', 'hours'],
  minutes: ['minute', 'minutes']
}

export function formatDateTime(isoString) {
  return isoString ? new Date(isoString).toUTCString() : ''
}

export function formatDate(isoString) {
  return isoString ? new Date(isoString).toDateString() : ''
}

function formatDuration(num, unit) {
  return `${num} ${DurationKeys[unit][num === 1 ? 0 : 1]} ago`
}

function remainingFormatDuration(num, unit) {
  return `${num} ${DurationKeys[unit][num === 1 ? 0 : 1]}`
}

function parseDate(date) {
  return isDate(date) ? date : new Date(date)
}

export function formatTimeDiff(t1, t2 = new Date()) {
  const t1Parsed = parseDate(t1)
  const t2Parsed = parseDate(t2)
  if (!isValid(t1Parsed) || !t1) {
    return '-'
  }
  const days = diffInDays(t2Parsed, t1Parsed)
  if (days > 365) {
    return formatDuration(diffInYears(t2Parsed, t1Parsed), 'years')
  }
  if (days > 31) {
    return formatDuration(diffInMonths(t2Parsed, t1Parsed), 'months')
  }
  if (days > 6) {
    return formatDuration(diffInWeeks(t2Parsed, t1Parsed), 'weeks')
  }
  if (days < 1) {
    const hours = diffInHours(t2Parsed, t1Parsed)
    if (hours < 1) {
      const minutes = diffInMinutes(t2Parsed, t1Parsed)
      if (minutes < 0) {
        return 'N/A'
      }
      return formatDuration(minutes, 'minutes')
    }
    return formatDuration(hours, 'hours')
  }
  return formatDuration(days, 'days')
}

export function formatRemainingTime(t2, t1 = new Date()) {
  const t1Parsed = parseDate(t1)
  const t2Parsed = parseDate(t2)
  if (!isValid(t1Parsed)) {
    return '-'
  }
  const days = diffInDays(t2Parsed, t1Parsed)
  const hours = diffInHours(t2Parsed, t1Parsed)
  switch (true) {
    case days > 365:
      return remainingFormatDuration(diffInYears(t2Parsed, t1Parsed), 'years')
    case days > 31:
      return remainingFormatDuration(diffInMonths(t2Parsed, t1Parsed), 'months')
    case days > 6:
      return remainingFormatDuration(diffInWeeks(t2Parsed, t1Parsed), 'weeks')
    case days < 1:
      if (days < 0) {
        return 'expired'
      }
      if (hours < 1) {
        const minutes = diffInMinutes(t2Parsed, t1Parsed)
        if (minutes <= 0) {
          return 'expired'
        } else {
          return remainingFormatDuration(minutes, 'minutes')
        }
      }
      return remainingFormatDuration(hours, 'hours')
    default:
      return remainingFormatDuration(days, 'days')
  }
}
