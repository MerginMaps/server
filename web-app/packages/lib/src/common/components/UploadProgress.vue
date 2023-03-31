<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <v-snackbar
    v-if="list.length"
    bottom
    right
    auto-height
    :timeout="-1"
    :value="visible"
  >
    <v-layout column>
      <v-layout
        class="py-1 row align-center justify-space-between"
        v-for="(upload, project) in uploads"
        :key="project"
      >
        <span>{{ project }}</span>
        <v-progress-circular
          :size="55"
          :width="8"
          :value="(upload.loaded / upload.total) * 100"
          color="teal"
        >
          {{ Math.floor((upload.loaded / upload.total) * 100) }}%
        </v-progress-circular>
      </v-layout>
    </v-layout>
  </v-snackbar>
</template>

<script lang="ts">
import debounce from 'lodash/debounce'
import Vue from 'vue'
import { mapState } from 'vuex'

export default Vue.extend({
  name: 'upload-progress',
  data() {
    return {
      visible: false
    }
  },
  computed: {
    ...mapState('projectModule', ['uploads']),
    list() {
      return Object.values(this.uploads)
    },
    uploading() {
      return this.list.some((u) => u.running)
    }
  },
  watch: {
    uploading: 'updateVisibility'
  },
  methods: {
    updateVisibility: debounce(function (value) {
      this.visible = value
    }, 500)
  }
})
</script>

<style lang="scss" scoped>
::v-deep {
  .v-snack__content {
    padding: 0.75em 1em;
  }

  .v-progress-circular__overlay {
    transition-duration: 0.2s;
  }
}

.row:not(:last-child) {
  border-bottom: 1px solid #444;
}
</style>
