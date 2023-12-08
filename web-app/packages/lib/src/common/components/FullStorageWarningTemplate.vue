<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <app-container v-if="open">
    <app-section ground>
      <PMessage severity="warn" @close="open = false">
        <p>
          <span class="font-semibold"
            >Your storage is almost full ({{ usage }}%).</span
          >
          Soon you will not be able to sync your projects.
          <slot name="buttons"></slot></p
      ></PMessage>
    </app-section>
  </app-container>
</template>

<script lang="ts">
import { defineComponent, ref } from 'vue'

import { AppContainer, AppSection } from '@/common/components'

export default defineComponent({
  name: 'FullStorageWarningTemplate',
  components: {
    AppContainer,
    AppSection
  },
  props: {
    usage: Number
  },
  setup() {
    /** Handle open state with connection to message close button */
    const open = ref(true)
    return {
      open
    }
  }
})
</script>

<style scoped></style>
