<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <div />
</template>

<script lang="ts">
import Vue from 'vue'
import { mapState, mapActions } from 'vuex'

export default Vue.extend({
  name: 'CheckForUpdates',
  computed: {
    ...mapState('instanceModule', ['configData'])
  },
  methods: {
    ...mapActions('adminModule', ['getCheckUpdateFromCookies', 'checkVersions'])
  },
  created() {
    this.getCheckUpdateFromCookies()
    this.checkVersions({
      major: this.configData.major,
      minor: this.configData.minor,
      fix: this.configData.fix ?? null
    })
  }
})
</script>

<style scoped></style>
