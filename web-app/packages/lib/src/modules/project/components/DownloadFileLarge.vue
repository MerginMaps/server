<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <PToast group="download-large-error" position="top-center">
    <template #message>
      <p>
        The project is too large to download. Please use direct download with
        our Python API Client or QGIS plugin instead.
        <a
          href="https://merginmaps.com/blog/support-tip-downloading-a-previous-version-of-your-project"
          target="_blank"
          class="font-semibold"
          >Read our blog for more details</a
        >.
      </p>
    </template>
  </PToast>
</template>

<script lang="ts">
import { defineComponent } from 'vue'

// we need to use options api here , because useToast is not properly handled multiple toast services
export default defineComponent({
  name: 'DownloadFileLarge'
})
</script>

<style lang="scss" scoped></style>
