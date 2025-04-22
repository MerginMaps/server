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
import { defineComponent } from 'vue'

import { useProjectStore } from '@/modules/project/store'

// we need to use options api here , because useToast is not properly handled multiple toast services
export default defineComponent({
  name: 'DownloadProgress',
  data() {
    return {
      projectStore: useProjectStore()
    }
  },
  methods: {
    open() {
      this.$toast.add({
        group: 'download-progress',
        severity: 'info',
        summary: 'Downloading project archive',
        detail: 'Please wait while your project is being downloaded.',
        life: undefined
      })
    },
    close() {
      this.projectStore.cancelDownloadArchive()
    }
  },
  watch: {
    'projectStore.projectDownloading'(value) {
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
