// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

export default {
  data() {
    return {
      errors: {},
      errorMsg: null
    }
  },
  methods: {
    clearErrors() {
      this.errors = {}
      this.errorMsg = null
    },
    handleError(err, generalMsg = 'Error') {
      if (typeof err.response.data === 'object') {
        // two types of error responses
        if (typeof err.response.data.status === 'number') {
          this.errorMsg = err.response.data.detail
        } else {
          this.errors = err.response.data
        }
      } else {
        this.errorMsg = err.response.data || generalMsg
      }
    }
  }
}
