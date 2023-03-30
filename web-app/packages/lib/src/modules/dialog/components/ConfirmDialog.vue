<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <v-card>
    <v-card-title class="text-h5">{{ headline }}</v-card-title>
    <v-card-text v-html="text" />
    <v-card-actions>
      <v-text-field
        v-if="confirmField"
        autofocus
        :label="confirmField.label"
        v-model="confirmValue"
        style="margin-left: 15px"
      />
      <v-spacer />
      <v-btn text @click="close">
        {{ cancelText }}
      </v-btn>
      <v-btn :disabled="!isConfirmed" color="primary" @click="confirm">
        {{ confirmText }}
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script lang="ts">
import Vue from 'vue'
import { mapActions } from 'vuex'

export default Vue.extend({
  name: 'confirm-dialog',
  props: {
    text: String,
    confirmField: Object,
    confirmText: {
      type: String,
      default: 'Ok'
    },
    cancelText: {
      type: String,
      default: 'Cancel'
    },
    headline: {
      type: String,
      default: 'Confirm'
    }
  },
  data() {
    return {
      confirmValue: ''
    }
  },
  computed: {
    isConfirmed() {
      return this.confirmField
        ? this.confirmField.expected === this.confirmValue
        : true
    }
  },
  methods: {
    ...mapActions('dialogModule', ['close']),

    confirm() {
      this.close()
      this.$emit('confirm')
    }
  }
})
</script>
