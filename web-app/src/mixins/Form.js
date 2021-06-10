// Copyright (C) 2018 Lutra Consulting Limited. All rights reserved.
// Do not distribute without the express permission of the author.

export default {
  data () {
    return {
      errors: {},
      errorMsg: null
    }
  },
  methods: {
    clearErrors () {
      this.errors = {}
      this.errorMsg = null
    },
    handleError (err, generalMsg = 'Error') {
      if (typeof err.response.data === 'object') {
        this.errors = err.response.data
      } else {
        this.errorMsg = err.response.data || generalMsg
      }
    }
  }
}
