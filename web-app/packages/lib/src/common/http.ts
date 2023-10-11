// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import axios, { AxiosInstance, AxiosResponse } from 'axios'
import axiosRetry, { isNetworkError, isRetryableError } from 'axios-retry'
import https from 'https'

import { CustomError } from '@/common/errors'

export interface HttpService extends AxiosInstance {
  absUrl?: (url: string) => string
  appendParams?: (url: string, params: Record<string, any>) => string
}

const HTTP: HttpService = axios.create({
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

axiosRetry(HTTP, {
  retries: 0,
  retryDelay: () => {
    return 60 * 1000
  }
})

export function initRequestInterceptors(
  isMaintenance: () => boolean,
  ignoredUrl: string[]
) {
  HTTP.interceptors.request.use(
    (request) => {
      if (
        isMaintenance() &&
        request.method !== 'get' &&
        !ignoredUrl.some((url) => request.url.includes(url))
      ) {
        // mimic regular response object, server will not be called
        const custError = new CustomError('reason', {
          data: {
            detail:
              'The service is currently in read-only mode for maintenance. Upload and update functions are not available at this time. Please try again later.'
          },
          status: 503
        })
        return Promise.reject(custError)
      }
      return request
    },
    (error) => {
      return Promise.reject(error)
    }
  )
}

export function initResponseInterceptors(authErrorCallback: () => void) {
  HTTP.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.response) {
        // detail is returned from flask_wtf library
        if (
          error.response.status === 400 &&
          error.response.data?.detail === 'The CSRF token has expired.'
        ) {
          return HTTP.get('/app/auth/refresh/csrf').then((resp) => {
            HTTP.defaults.headers.common['X-CSRF-Token'] = resp.data.csrf
            const config = error.config
            return restartRequest(config)
              .then((resp) => {
                return resp
              })
              .catch((err) => {
                return Promise.reject(err)
              })
          })
        } else {
          const { status } = error.response
          if (status === 401) {
            authErrorCallback()
          }
          return Promise.reject(error)
        }
      } else {
        return Promise.reject(error)
      }
    }
  )
}

export function getHttpService() {
  return HTTP
}

export function initCsrfToken(response: AxiosResponse) {
  const http = getHttpService()
  http.defaults.headers.common['X-CSRF-Token'] =
    response.headers['x-csrf-token']
}

export function postRetryCond(error) {
  if (!error.config) {
    return false
  }
  return isNetworkError(error) || isRetryableError(error)
}

export function getDefaultRetryOptions() {
  return {
    'axios-retry': {
      retries: 5,
      retryCondition: (error) => postRetryCond(error)
    }
  }
}

function restartRequest(request) {
  request.headers = HTTP.defaults.headers.common
  // create object from origin request body again
  request.data = request.data ? JSON.parse(request.data) : request.data
  return HTTP.request(request)
}

/**
 * Axios default status codes overwrite for 207
 */
export function validateStatus(status: number): boolean {
  return (status >= 200 && status < 207) || (status > 207 && status < 300)
}
