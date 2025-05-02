<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <PToast group="download-progress" position="top-center" @close="close">
    <template #icon>
      <PProgressSpinner style="width: 40px; height: 40px" />
    </template>
  </PToast>
</template>

<script lang="ts">
import { mapActions, mapState } from 'pinia'
import { defineComponent } from 'vue'

import { useProjectStore } from '@/modules/project/store'

// we need to use options api here , because useToast is not properly handled multiple toast services
export default defineComponent({
  name: 'DownloadProgress',
  computed: {
    ...mapState(useProjectStore, [
      'project',
      'projectDownloading',
      'projectDownloadingVersion'
    ])
  },
  methods: {
    ...mapActions(useProjectStore, ['cancelDownloadArchive']),
    open() {
      this.$toast.add({
        group: 'download-progress',
        severity: 'info',
        summary: `Preparing to download your project ${
          this.projectDownloadingVersion
            ? `(version ${this.projectDownloadingVersion})`
            : ''
        }`,
        detail: `Your download will begin automatically once it's ready. Please keep this window open.`,
        life: undefined
      })
    },
    close() {
      this.cancelDownloadArchive()
    }
  },
  watch: {
    projectDownloading(value) {
      if (value) {
        this.open()
      } else {
        this.$toast.removeGroup('download-progress')
      }
    }
  }
})
</script>

<style lang="scss" scoped></style>
