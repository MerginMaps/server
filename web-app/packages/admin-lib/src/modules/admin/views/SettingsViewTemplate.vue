<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <admin-layout>
    <page-view
      :style="`overflow-y: auto; padding-right:20px; margin-right: 0px;`"
    >
      <v-layout class="column fill-height ml-10">
        <slot />
      </v-layout>
    </page-view>
  </admin-layout>
</template>

<script lang="ts">
import { PageView } from '@mergin/lib'
import Vue from 'vue'

import AdminLayout from '@/modules/admin/components/AdminLayout.vue'

export default Vue.extend({
  name: 'SettingsViewTemplate',
  components: {
    PageView,
    AdminLayout
  }
})
</script>

<style lang="scss" scoped></style>
