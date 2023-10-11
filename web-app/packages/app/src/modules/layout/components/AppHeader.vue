<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <app-header-template :isPrimary="isPrimary" :renderNamespace="false" />
</template>

<script lang="ts">
import { AppHeaderTemplate } from '@mergin/lib'
import { defineComponent } from 'vue'

export default defineComponent({
  name: 'AppHeader',
  props: {
    isPrimary: {
      type: Boolean,
      default: true
    }
  },
  components: { AppHeaderTemplate }
})
</script>

<style lang="scss" scoped></style>
