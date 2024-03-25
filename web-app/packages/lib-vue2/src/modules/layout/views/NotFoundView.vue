<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <custom-page>
    <v-card style="min-width: 300px" class="text-center">
      <v-card-title class="justify-center primary--text font-weight-bold ml-3">
        <h3>Page not found</h3>
      </v-card-title>
      <v-card-text>
        <p>This page does not exist, check your url for mistakes, please.</p>
      </v-card-text>
      <v-card-actions class="justify-center">
        <v-btn
          v-if="displayBackButton"
          data-cy="login-form-btn-back-dashboard"
          color="primary"
          :to="{ name: 'dashboard' }"
          >Back to Dashboard
        </v-btn>
      </v-card-actions>
    </v-card>
  </custom-page>
</template>

<script lang="ts">
import { mapState } from 'pinia'
import { defineComponent } from 'vue'

import CustomPage from '@/common/components/CustomPage.vue'
import { useUserStore } from '@/modules/user/store'

export default defineComponent({
  name: 'NotFoundView',
  components: { CustomPage },
  computed: {
    ...mapState(useUserStore, ['loggedUser']),
    displayBackButton() {
      return this.loggedUser
    }
  }
})
</script>

<style scoped></style>
