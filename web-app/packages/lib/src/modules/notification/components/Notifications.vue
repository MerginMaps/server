<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <v-snackbar
    :model-value="isOpen"
    v-bind="params"
    @update:model-value="closeNotification"
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
import { mapActions, mapState } from 'pinia'
import { defineComponent } from 'vue'

import { useNotificationStore } from '@/modules/notification/store'

export default defineComponent({
  computed: {
    ...mapState(useNotificationStore, ['isOpen', 'params', 'text']),

    buttonColor() {
      return this.params?.buttonColor ?? 'yellow'
    },
    timeout() {
      return this.params?.timeout ?? 3000
    }
  },
  methods: {
    ...mapActions(useNotificationStore, ['closeNotification'])
  }
})
</script>
