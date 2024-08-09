<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <admin-layout>
    <v-layout class="column fill-height ml-10">
      <slot />
    </v-layout>
  </admin-layout>
</template>

<script lang="ts">
import { defineComponent } from 'vue'

import AdminLayout from '@/modules/admin/components/AdminLayout.vue'

export default defineComponent({
  name: 'SettingsViewTemplate',
  components: {
    AdminLayout
  }
})
</script>

<style lang="scss" scoped></style>
