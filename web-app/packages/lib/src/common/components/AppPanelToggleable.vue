<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <PPanel
    toggleable
    v-bind="$props"
    :pt="{
      header(options) {
        return {
          class: [
            'surface-section border-none p-4',
            // Toggle border radius by open / closed panel
            options.state.d_collapsed
              ? 'border-round-2xl'
              : 'border-round-top-2xl'
          ]
        }
      },
      content: {
        class: 'border-none border-round-bottom-2xl p-4 pt-2'
      }
    }"
  >
    <template #header>
      <h3 class="text-color-forest font-semibold m-0">
        <slot name="header"></slot>
      </h3>
    </template>
    <template v-if="$slots.footer" #footer>
      <slot name="footer"></slot>
    </template>
    <template #icons>
      <slot name="icons"></slot>
    </template>
    <slot></slot>
    <template #togglericon="{ collapsed }">
      <i
        :class="[
          'font-semibold text-color-forest ti',
          collapsed ? 'ti-chevron-down' : 'ti-chevron-up'
        ]"
      ></i>
    </template>
  </PPanel>
</template>

<script lang="ts" setup></script>
