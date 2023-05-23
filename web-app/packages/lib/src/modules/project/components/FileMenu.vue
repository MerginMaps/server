<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <v-menu
    v-model="showMenu"
    :position-x="x"
    :position-y="y"
    position="absolute"
    offset-y
    :min-width="150"
  >
    <v-list>
      <v-list-item @click="deleteFile">
        <v-list-item-title>Delete</v-list-item-title>
      </v-list-item>
    </v-list>
  </v-menu>
</template>

<script lang="ts">
import { mapActions } from 'pinia'
import { defineComponent } from 'vue'

import { useProjectStore } from '@/modules/project/store'

export default defineComponent({
  data() {
    return {
      showMenu: false,
      x: 0,
      y: 0,
      file: null
    }
  },
  methods: {
    ...mapActions(useProjectStore, ['deleteFiles']),
    open(evt, file) {
      this.showMenu = true
      this.x = evt.clientX
      this.y = evt.clientY
      this.file = file
    },
    deleteFile() {
      this.deleteFiles({ files: [this.file.path] })
    }
  }
})
</script>
