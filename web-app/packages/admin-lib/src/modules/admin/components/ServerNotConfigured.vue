<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <div class="banner" v-if="displayBanner">
    <v-card class="cardWrapper" elevation="0" rounded>
      <v-card-title class="text-h6 font-weight-bold">
        <v-icon class="orange--text mr-2">error</v-icon>
        Server is not properly configured
      </v-card-title>
      <v-card-subtitle class="ml-8 black--text">
        Your server is not configured properly for use in the production
        environment. Read more in the documentation how to properly set up the
        deployment.
      </v-card-subtitle>
      <v-card-actions class="ml-7 pb-4">
        <v-btn
          class="orange white--text buttonWrapper"
          :href="docsLinkDocumentation"
        >
          Read documentation
        </v-btn>
        <v-spacer />
        <v-btn text class="orange--text buttonWrapper" @click="dismiss">
          Dismiss
        </v-btn>
      </v-card-actions>
    </v-card>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue'
import { mapActions, mapState } from 'vuex'

export default defineComponent({
  name: 'ServerNotConfigured',
  methods: {
    ...mapActions('adminModule', [
      'setServerConfiguredCookies',
      'getServerConfiguredCookies'
    ]),
    dismiss(e) {
      e.preventDefault()
      this.setServerConfiguredCookies()
    }
  },
  created() {
    this.getServerConfiguredCookies()
  },
  computed: {
    ...mapState('instanceModule', ['configData']),
    ...mapState('adminModule', ['isServerConfigHidden']),
    docsLinkDocumentation(): string {
      return `${this.configData?.docs_url ?? ''}/dev/mergince`
    },
    displayBanner(): boolean {
      return !this.configData?.server_configured && !this.isServerConfigHidden
    }
  }
})
</script>

<style lang="scss" scoped>
.banner {
  display: flex;
  justify-content: center;
}
.cardWrapper {
  margin-top: 20px;
  margin-bottom: 20px;
  background-color: #fffaf0;
}
.warningIcon {
  background-color: #fffaf0;
}
.buttonWrapper {
  flex: 1;
}
</style>
