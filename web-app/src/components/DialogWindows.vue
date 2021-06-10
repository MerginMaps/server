# Copyright (C) 2018 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

<template>
  <v-dialog
    :value="open"
    v-bind="dialogProps"
    @input="close"
  >
    <div
      v-if="params"
      :is="params.component"
      v-bind="params.props"
      v-on="params.listeners"
    />
  </v-dialog>
</template>

<script>
import Vue from 'vue'
import ConfirmDialog from '@/components/ConfirmDialog'

export default {
  data () {
    return {
      open: false,
      params: null
    }
  },
  computed: {
    dialogProps () {
      return this.params ? this.params.dialog : {}
    }
  },
  created () {
    Vue.prototype.$dialog = this
  },
  methods: {
    _open (params) {
      this.params = params
      this.open = true
    },
    show (component, params) {
      this._open({ component, ...params })
    },
    prompt (params) {
      this._open({ component: ConfirmDialog, ...params })
    },
    close () {
      this.open = false
      if (this.params.dialog && !this.params.dialog.keepAlive) {
        setTimeout(() => {
          this.params = null
        }, 300)
      }
    }
  }
}
</script>
