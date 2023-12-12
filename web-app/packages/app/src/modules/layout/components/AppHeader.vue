<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <app-header-template :renderNamespace="false" />
</template>

<script lang="ts">
import { AppHeaderTemplate } from '@mergin/lib'
import { defineComponent } from 'vue'

export default defineComponent({
  name: 'AppHeader',
  components: { AppHeaderTemplate }
})
</script>

<style lang="scss" scoped></style>
