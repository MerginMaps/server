<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <div>
    <slot name="usageInfo" />
    <slot name="content"></slot>
    <community-banner />
    <dashboard-footer />
  </div>
</template>

<script lang="ts" setup>
import { DashboardFooter } from '@/modules/dashboard'
import CommunityBanner from '@/modules/project/components/CommunityBanner.vue'
</script>

<style scoped lang="scss"></style>
