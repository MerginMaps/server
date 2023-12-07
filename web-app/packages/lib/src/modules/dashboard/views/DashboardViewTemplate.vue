<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <div>
    <app-container>
      <slot name="usageInfo" />
    </app-container>
    <slot name="content"></slot>
    <dashboard-footer />
  </div>
</template>

<script lang="ts" setup>
import { AppContainer } from '@/common/components'
import { DashboardFooter } from '@/modules/dashboard'
</script>

<style scoped lang="scss"></style>
