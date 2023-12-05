<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <div>
    <app-container>
      <slot name="usageInfo" />
    </app-container>
    <app-container><slot name="content"></slot></app-container>
    <footer>
      <app-container>
        <app-section class="grid-nogutter flex align-items-center">
          <div
            class="dashboard-view-footer-mobile relative col-12 lg:col-3 align-self-start"
          >
            <img
              src="@/assets/footer-mobile.png"
              class="absolute top-0 left-2rem"
            />
          </div>
          <div class="col-12 lg:col-5">
            <h2 class="text-color text-sm font-semibold">
              Download Mergin Maps
            </h2>
            <p class="text-color-secondary text-sm">
              Capture geo-info easily through your mobile/tablet with the Mergin
              Maps Input app.
            </p>
          </div>
          <div class="col-12 lg:col-4">
            <a
              href="https://apps.apple.com/us/app/input/id1478603559?ls=1&utm_source=mergin-website&utm_medium=banner&utm_campaign=input"
              target="_blank"
              class="mr-1"
              ><img src="@/assets/appstore.jpg"
            /></a>
            <a
              href="https://play.google.com/store/apps/details?id=uk.co.lutraconsulting&utm_source=mergin-website&utm_medium=banner&utm_campaign=input"
              target="_blank"
              ><img src="@/assets/googleplay.jpg"
            /></a>
          </div> </app-section
      ></app-container>
    </footer>
  </div>
</template>

<script lang="ts" setup>
import { AppContainer, AppSection } from '@/common/components'
</script>

<style scoped lang="scss">
.dashboard-view-footer-mobile {
  margin-top: -1.5rem;
  min-height: 100px;
}
</style>
