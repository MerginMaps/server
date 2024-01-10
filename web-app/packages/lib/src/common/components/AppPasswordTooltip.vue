<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <label class="flex align-items-center" :for="'for'"
    ><slot name="label"></slot>&nbsp;
    <i
      class="ti ti-info-circle-filled cursor-pointer text-color-medium-green hover:text-color text-base"
      :style="{ color: 'var(--medium-green-color)' }"
      v-tooltip="{
        value: tooltip,
        escape: false
      }"
  /></label>
</template>

<script lang="ts" setup>
defineProps<{ for: string }>()
const tooltip = `
  <ul>
    <li>Password must be at least 8 characters long.</li>
    <li>Password must contain at least 3 character categories among the following:</li>
      <ul>
        <li>Lowercase characters (a-z)</li>
        <li>Uppercase characters (A-Z)</li>
        <li>Digits (0-9)</li>
        <li>Special characters</li>
      </ul>
  </ul>
`
</script>
