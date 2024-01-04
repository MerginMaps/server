<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <section>
    <PPanel
      :toggleable="!!$slots.default"
      :collapsed="true"
      :pt="{
        header(options) {
          return {
            class: [
              'surface-section border-none p-4',
              // Toggle border radius by open / closed panel
              options.state.d_collapsed
                ? 'border-round-xl'
                : 'border-round-top-xl'
            ]
          }
        },
        content: {
          class: 'border-none border-round-bottom-2xl p-4 pt-2'
        }
      }"
    >
      <template v-if="!$slots.header" #header>
        <header
          class="w-full flex flex-column lg:flex-row align-items-center justify-content-between row-gap-4"
        >
          <div
            class="flex flex-column lg:flex-row align-items-center row-gap-2"
          >
            <div class="flex lg:mr-4">
              <slot name="header-image"></slot>
            </div>
            <div class="flex flex-column gap-2 text-center lg:text-left">
              <h3 class="text-color text-sm font-semibold m-0">
                <slot name="title"></slot>
              </h3>
              <p class="text-xs m-0 opacity-80">
                <slot name="description"></slot>
              </p>
            </div>
          </div>
          <slot name="header-actions"></slot>
        </header>
      </template>
      <!-- Header without additional styles -->
      <template v-else #header><slot name="header"></slot></template>
      <slot></slot>
      <template v-if="$slots.footer" #footer>
        <slot name="footer"></slot>
      </template>
      <template #icons>
        <slot name="icons"></slot>
      </template>
      <template #togglericon="{ collapsed }">
        <i
          :class="[
            'font-semibold text-color-forest ti',
            collapsed ? 'ti-chevron-down' : 'ti-chevron-up'
          ]"
        ></i>
      </template>
    </PPanel>
  </section>
</template>

<script lang="ts" setup></script>
