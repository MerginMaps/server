<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <div />
</template>

<script lang="ts">
import { useInstanceStore } from '@mergin/lib-vue2'
import { mapState, mapActions } from 'pinia'
import { defineComponent } from 'vue'

import { useAdminStore } from '@/modules/admin/store'

export default defineComponent({
  name: 'CheckForUpdates',
  computed: {
    ...mapState(useInstanceStore, ['configData'])
  },
  methods: {
    ...mapActions(useAdminStore, ['getCheckUpdateFromCookies', 'checkVersions'])
  },
  created() {
    this.getCheckUpdateFromCookies()
    this.checkVersions({
      major: this.configData?.major,
      minor: this.configData?.minor,
      fix: this.configData?.fix ?? null
    })
  }
})
</script>

<style scoped></style>
