<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <section class="app-section-banner">
    <PPanel
      v-bind="$props"
      :collapsed="$props.collapsed || !$slots.default"
      :pt="{
        header(options) {
          return {
            class: [
              severity === 'primary'
                ? 'app-section-banner-primary'
                : 'surface-section text-color',
              'border-none p-4',
              // Toggle border radius by open / closed panel
              options.state.d_collapsed
                ? 'border-round-xl'
                : 'border-round-top-xl border-bottom-2 surface-border'
            ]
          }
        },
        icons: 'flex align-items-center ml-1 gap-1',
        content: 'border-none border-round-bottom-2xl p-4'
      }"
    >
      <template v-if="!$slots.header" #header>
        <header
          :class="[
            'w-full',
            $slots['header-actions'] &&
              'flex flex-column lg:flex-row lg:align-items-center justify-content-between gap-4'
          ]"
        >
          <div
            :class="[
              $slots['header-image'] &&
                'flex flex-column lg:flex-row gap-4 lg:align-items-center'
            ]"
          >
            <div v-if="$slots['header-image']" class="flex align-items-center">
              <slot name="header-image"></slot>
            </div>
            <div :class="['flex flex-column gap-2 lg:gap-0']">
              <h3 class="title-t3">
                <slot name="title"></slot>
              </h3>
              <p v-if="$slots.description" class="paragraph-p6 opacity-80">
                <slot name="description"></slot>
              </p>
            </div>
          </div>
          <slot name="header-actions"></slot>
        </header>
      </template>
      <!-- Header without additional styles -->
      <template v-else #header><slot name="header"></slot></template>
      <div class="paragraph-p6 opacity-80"><slot></slot></div>

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

<script lang="ts" setup>
import { PanelProps } from 'primevue/panel'

type Severity = 'info' | 'primary'

defineProps<PanelProps & { severity?: Severity }>()
</script>

<style lang="scss">
.app-section-banner {
  h3 {
    color: var(--text-color);
  }
}
.app-section-banner-primary {
  color: #ffffff;
  background: linear-gradient(
    266deg,
    #6e9991 33.35%,
    var(--forest-color) 68.86%
  );
  & h3 {
    color: #ffffff;
  }
}
</style>
