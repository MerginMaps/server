# Copyright (C) 2018 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

<template>
  <v-snackbar
    :value="open"
    v-bind="params"
    @input="_close"
    :timeout="timeout"
  >
    <template v-if="params">
      <span v-text="params.text"/>
      <v-btn
        v-if="params.action"
        text
        color="yellow"
        @click="params.action.handler"
      >
        {{ params.action.text }}
      </v-btn>
      <v-btn
        v-else
        text
        :color="contrastColor"
        @click="_close"
      >
        Close
      </v-btn>
    </template>
  </v-snackbar>
</template>

<script>
import Vue from 'vue'

export default {
  data () {
    return {
      params: null,
      action: null,
      timeout: 3000
    }
  },
  computed: {
    open () {
      return Boolean(this.params)
    },
    contrastColor () {
      return (this.params && this.params.contrastColor) || 'yellow'
    }
  },
  mounted () {
    Vue.prototype.$notification = this
  },
  methods: {
    _close () {
      this.params = null
      this.action = null
      this.timeout = 3000
    },
    _open (params) {
      if (this.open) {
        if (this.params.text === params.text) {
          // ignore same notifications
          return
        }
        this._close()
        setTimeout(() => {
          this._open(params)
        }, 300)
      } else {
        this.params = params
        if (params.timeout) this.timeout = params.timeout
      }
    },
    show (text, opts = {}) {
      this._open({ ...opts, text })
    },
    warn (text, opts = {}) {
      this._open({ ...opts, text, color: 'orange', contrastColor: 'black' })
    },
    error (text, opts = {}) {
      this._open({ ...opts, text, color: 'red darken-4' })
    },
    displayResult (result) {
      if (result.success) {
        this.show(result.message)
      } else {
        this.error(result.message, { timeout: 5000 })
      }
    }
  }
}
</script>
