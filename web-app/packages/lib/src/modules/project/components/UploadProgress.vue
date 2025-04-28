<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <PToast group="upload-progress" v-if="list.length" position="top-center">
    <template #message="{ message }">
      <i :class="['p-toast-message-icon', 'ti ti-cloud-upload']" />
      <div
        class="p-toast-message-text flex flex-column row-gap-2"
        data-pc-section="text"
      >
        <span class="p-toast-summary" data-pc-section="summary">{{
          message.summary
        }}</span>
        <template v-for="(upload, project) in uploads" :key="project">
          <span class="opacity-80 mb-2">{{ project }}</span>
          <PProgressBar
            :value="Math.round((upload.loaded / upload.total) * 100)"
          ></PProgressBar>
        </template>
      </div>
    </template>
  </PToast>
</template>

<script lang="ts">
import debounce from 'lodash/debounce'
import { mapState } from 'pinia'
import { defineComponent } from 'vue'

import { useProjectStore } from '@/modules/project/store'

export default defineComponent({
  name: 'upload-progress',
  computed: {
    ...mapState(useProjectStore, ['uploads']),
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
    open() {
      this.$toast.add({
        group: 'upload-progress',
        severity: 'info',
        summary: 'Uploading data to project.'
      })
    },
    close() {
      this.$toast.removeGroup('upload-progress')
    },
    updateVisibility: debounce(function (value) {
      if (!value) {
        this.close()
      } else {
        this.open()
      }
    }, 500)
  }
})
</script>

<style lang="scss" scoped></style>
