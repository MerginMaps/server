// Copyright (C) 2018 Lutra Consulting Limited. All rights reserved.
// Do not distribute without the express permission of the author.

import http from './http'

const initialize = new Promise((resolve, reject) => {
  http.get('/dev/init')
    .then(resp => {
      http.defaults.headers.common['X-CSRF-Token'] = resp.headers['x-csrf-token']
      // eslint-disable-next-line no-undef
      resolve(resp.data)
    })
    .catch(reject)
})

export default () => initialize
