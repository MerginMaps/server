<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <profile-view-template :name="name">
    <template #additionalContent>
      <profile-access-requests-row />
    </template>
  </profile-view-template>
</template>

<script lang="ts">
import { ProfileViewTemplate, ProfileAccessRequestsRow } from '@mergin/lib'
import { defineComponent } from 'vue'

export default defineComponent({
  name: 'ProfileView',
  components: {
    ProfileViewTemplate,
    ProfileAccessRequestsRow
  },
  props: {
    name: String
  }
})
</script>
