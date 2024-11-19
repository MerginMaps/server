<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <profile-view-template>
    <template #additionalContent>
      <profile-access-requests-row />
    </template>
  </profile-view-template>
</template>

<script setup lang="ts">
import { ProfileViewTemplate, ProfileAccessRequestsRow } from '@mergin/lib'
</script>
