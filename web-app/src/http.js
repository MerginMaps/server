// Copyright (C) 2018 Lutra Consulting Limited. All rights reserved.
// Do not distribute without the express permission of the author.

import axios from 'axios'
import https from 'https'
import axiosRetry, { isNetworkError, isRetryableError } from 'axios-retry'


const HTTP = axios.create({
  baseURL: '',
  withCredentials: true,
  httpsAgent: new https.Agent({
    rejectUnauthorized: false
  }),
  headers: { 'X-Client': 'vue' },
  maxContentLength: 4 * 1024 * 1024 * 1024
})

HTTP.absUrl = function (url) {
  return HTTP.defaults.baseURL + url
}

HTTP.appendParams = function (url, params) {
  const u = new URL(url)
  for (const key in params) {
    if (params[key] !== undefined) {
      u.searchParams.append(key, params[key])
    }
  }
  return u.href
}

axiosRetry(HTTP, { retries: 0, retryDelay: () => { return 60 * 1000 } })

export default HTTP

export function postRetryCond (error) {
  if (!error.config) {
    return false
  }
  return isNetworkError(error) || isRetryableError(error)
}
