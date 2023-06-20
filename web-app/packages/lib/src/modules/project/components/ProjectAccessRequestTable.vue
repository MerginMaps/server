<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <project-access-request-table-template
    :namespace="namespace"
    @accept-access-request-error="onAcceptAccessRequestError"
  />
</template>

<script lang="ts">
import { AxiosError } from 'axios'
import Vue from 'vue'
import { mapActions } from 'vuex'

import ProjectAccessRequestTableTemplate from './ProjectAccessRequestTableTemplate.vue'

export default Vue.extend({
  name: 'ProjectAccessRequestTable',
  components: { ProjectAccessRequestTableTemplate },
  props: {
    namespace: {
      type: String,
      default: null
    }
  },
  methods: {
    ...mapActions('notificationModule', ['error']),

    // TODO: Add more handlers from template, add more emits from template
    async onAcceptAccessRequestError(err: AxiosError) {
      const msg = err.response
        ? err.response.data?.detail
        : 'Failed to accept access request'
      this.error({ text: msg })
    }
  }
})
</script>

<style lang="scss" scoped></style>
