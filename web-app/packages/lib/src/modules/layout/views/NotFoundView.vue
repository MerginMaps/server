<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <article
    class="relative not-found-view flex align-items-center justify-content-center h-full"
  >
    <aside class="absolute top-0 left-0 m-4">
      <img src="@/assets/mm-logo.svg" />
    </aside>
    <div
      class="not-found-view-container flex flex-column align-items-center text-center row-gap-4 p-4 lg:p-0"
    >
      <header>
        <h1 class="headline-h1">Ooops, it seems the GPS has lost its way.</h1>
      </header>
      <img src="@/assets/map-circle.svg" alt="Not found" />
      This page does not exist, check your url for mistakes, please.
      <PButton
        v-if="displayBackButton"
        data-cy="login-form-btn-back-dashboard"
        @click="$router.push({ name: 'dashboard' })"
        >Back to Dashboard
      </PButton>
    </div>
  </article>
</template>

<script lang="ts">
import { mapState } from 'pinia'
import { defineComponent } from 'vue'

import { useUserStore } from '@/modules/user/store'

export default defineComponent({
  name: 'NotFoundView',
  computed: {
    ...mapState(useUserStore, ['loggedUser']),
    displayBackButton() {
      return this.loggedUser
    }
  }
})
</script>

<style scoped lang="scss">
.not-found-view {
  &-container {
    max-width: 480px;
    width: 100%;
  }
}
</style>
