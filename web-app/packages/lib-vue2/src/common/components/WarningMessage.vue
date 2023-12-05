<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <warning-message-template v-if="text">
    <template #message>
      <span style="margin-left: 10px"> {{ text }}</span>
    </template>
  </warning-message-template>
</template>

<script lang="ts">
import { defineComponent } from 'vue'

import WarningMessageTemplate from './WarningMessageTemplate.vue'

export default defineComponent({
  name: 'WarningMessage',
  components: { WarningMessageTemplate },
  props: {
    text: null
  }
})
</script>

<style scoped></style>
