<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <!-- Footer -->
  <footer v-if="!layoutStore.isClosedElement(elementId)" :id="elementId">
    <app-container>
      <app-section
        class="grid grid-nogutter flex align-items-center py-4 relative"
      >
        <div
          class="dashboard-view-footer-mobile relative col-12 xl:col-fixed align-self-start mb-2 xl:mb-0 flex justify-content-center"
        >
          <img
            src="@/assets/footer-mobile.webp"
            class="absolute top-0 left-2rem z-1"
          />

          <!-- Circle -->
          <div
            :class="[
              'dashboard-view-footer-mobile-circle',
              'border-circle absolute bottom-0 left-0 w-full'
            ]"
          ></div>
        </div>

        <div class="col-12 xl:col-5 mb-2 xl:mb-0 text-center xl:text-left">
          <h2 class="text-color paragraph-p5">
            Download Mergin Maps to your phone
          </h2>
          <p class="opacity-60 paragraph-p6">
            Capture geo-info easily through your mobile/tablet with our mobile
            app.
          </p>
        </div>

        <div class="col-12 xl:col-2 flex justify-content-center">
          <a
            href="https://apps.apple.com/us/app/input/id1478603559?ls=1&utm_source=mergin-website&utm_medium=banner&utm_campaign=input"
            target="_blank"
            class="mr-1"
            ><img :style="{ width: '100%' }" src="@/assets/appstore.jpg"
          /></a>
          <a
            href="https://play.google.com/store/apps/details?id=uk.co.lutraconsulting&utm_source=mergin-website&utm_medium=banner&utm_campaign=input"
            target="_blank"
            ><img :style="{ width: '100%' }" src="@/assets/googleplay.jpg"
          /></a>
        </div>

        <div
          class="dashboard-view-footer-close col-12 xl:col-1 flex justify-content-end"
        >
          <PButton
            icon="ti ti-x"
            text
            rounded
            plain
            aria-label="Close section"
            @click="closeElement"
            class="text-2xl"
          />
        </div> </app-section
    ></app-container>
  </footer>
</template>

<script setup lang="ts">
import { ref } from 'vue'

import { AppContainer, AppSection } from '@/common'
import { useLayoutStore } from '@/main'

const elementId = ref('dashboard-footer')
const layoutStore = useLayoutStore()
function closeElement() {
  layoutStore.closeElement(elementId.value)
}
</script>

<style lang="scss" scoped>
.dashboard-view-footer-mobile {
  margin-top: -1.5rem;
  min-height: 100px;
  width: 320px;

  &-circle {
    height: 320px;
    background-color: var(--primary-color);
  }
}
@media screen and (max-width: $xl) {
  .dashboard-view-footer-mobile {
    width: 100%;
  }
  .dashboard-view-footer-close {
    position: absolute;
    right: 5px;
    top: 5px;
  }
}
</style>
