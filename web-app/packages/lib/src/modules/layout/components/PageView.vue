<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <v-layout row justify-center align-start fill-height my-1>
    <slot name="left">
      <v-spacer class="hidden-md-and-down" />
    </slot>
    <slot />
    <slot name="right">
      <v-spacer class="hidden-md-and-down" />
    </slot>
    <a
      class="btn slack-link"
      v-if="slackLink"
      :href="slackLink"
      target="_blank"
    >
      <message-icon class="primary--text"></message-icon>
    </a>
    <p class="version hidden-md-and-down">Version: {{ version }}</p>
  </v-layout>
</template>

<script lang="ts">
import { defineComponent } from 'vue'
import { MessageIcon } from 'vue-tabler-icons'
import { mapState } from 'vuex'

export default defineComponent({
  components: { MessageIcon },
  computed: {
    ...mapState('instanceModule', ['configData']),
    version() {
      return `${this.configData?.server_type?.toUpperCase()} ${
        this.configData?.version
      }`
    },
    slackLink() {
      return import.meta.env.VITE_VUE_APP_JOIN_COMMUNITY_LINK
    }
  }
})
</script>

<style lang="scss" scoped>
.version {
  position: absolute;
  right: 0;
  bottom: 0;
  margin: 0.25em 0.5em;
  opacity: 0.75;
  font-size: 12px;
}

:deep(.main-content) {
  width: 800px;
  margin: 0 1em;
  @media (max-width: 1264px) {
    width: 100%;
  }
}

.slack-link {
  position: fixed;
  bottom: 25px;
  right: 20px;
  width: 60px;
  height: 60px;
  background: #eaebef;
  border-radius: 50%;
  text-decoration: none;
  text-align: center;
  display: flex;
  justify-content: center;
  align-items: center;
}
</style>
