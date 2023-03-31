<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <v-snackbar
    :value="isOpen"
    v-bind="params"
    @input="closeNotification"
    :timeout="timeout"
    style="overflow-y: auto"
  >
    <template v-if="params">
      <span v-text="text" />
      <v-btn
        v-if="params.action"
        text
        color="yellow"
        @click="params.action.handler"
      >
        {{ params.action.text }}
      </v-btn>
      <v-btn v-else text :color="buttonColor" @click="closeNotification">
        Close</v-btn
      >
    </template>
  </v-snackbar>
</template>

<script lang="ts">
import Vue from 'vue'
import { mapMutations, mapState } from 'vuex'

export default Vue.extend({
  computed: {
    ...mapState('notificationModule', ['isOpen', 'params', 'text']),

    buttonColor() {
      return this.params?.buttonColor ?? 'yellow'
    },
    timeout() {
      return this.params?.timeout ?? 3000
    }
  },
  methods: {
    ...mapMutations('notificationModule', ['closeNotification'])
  }
})
</script>
