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
import { mapActions } from 'pinia'
import { defineComponent } from 'vue'

import ProjectAccessRequestTableTemplate from './ProjectAccessRequestTableTemplate.vue'

import { getErrorMessage } from '@/common/error_utils'
import { useNotificationStore } from '@/modules/notification/store'

export default defineComponent({
  name: 'ProjectAccessRequestTable',
  components: { ProjectAccessRequestTableTemplate },
  props: {
    namespace: {
      type: String,
      default: null
    }
  },
  methods: {
    ...mapActions(useNotificationStore, ['error']),

    // TODO: Add more handlers from template, add more emits from template
    async onAcceptAccessRequestError(err: AxiosError) {
      this.error({
        text: getErrorMessage(err, 'Failed to accept access request')
      })
    }
  }
})
</script>

<style lang="scss" scoped></style>
