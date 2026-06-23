<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <PToast group="download-large-error" position="top-center">
    <template #message>
      <p>
        {{
          t(
            'TheProjectIsTooLargeToDownloadPleaseUseDirectDownloadWithOurPythonAPIClientOrQGISPluginInstead'
          )
        }}
        <a
          href="https://merginmaps.com/blog/support-tip-downloading-a-previous-version-of-your-project"
          target="_blank"
          class="font-semibold"
          >{{ t('ReadOurBlogForMoreDetails') }}</a
        >.
      </p>
    </template>
  </PToast>
</template>

<script lang="ts">
import { defineComponent } from 'vue'

import returnTranslation from '@/../../lang/translate'

// we need to use options api here , because useToast is not properly handled multiple toast services
export default defineComponent({
  name: 'DownloadFileLarge',
  methods: {
    t(key: string) {
      return returnTranslation(import.meta.env.VITE_LANG, key)
    }
  }
})
</script>

<style lang="scss" scoped></style>
