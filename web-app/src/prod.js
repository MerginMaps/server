// Copyright (C) 2018 Lutra Consulting Limited. All rights reserved.
// Do not distribute without the express permission of the author.

import http from './http'

const initialize = new Promise(resolve => {
  const data = window.app
  // eslint-disable-next-line no-undef
  http.defaults.headers.common['X-CSRF-Token'] = data.csrf
  delete data.csrf
  delete window.app
  resolve(data)
})

export default () => initialize
