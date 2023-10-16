<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <v-card v-on:keyup.enter="onCloneProject" data-cy="clone-dialog-card">
    <v-card-title>
      <span class="text-h5">Clone Project</span>
    </v-card-title>
    <v-card-text>
      <v-text-field
        autofocus
        label="new project"
        v-model="newProjectName"
        data-cy="clone-dialog-project-name"
      />
      <slot name="dynamic-items"></slot>
    </v-card-text>
    <v-card-actions>
      <v-spacer />
      <v-btn @click="close" data-cy="clone-dialog-close-btn"> Close </v-btn>
      <v-btn
        id="clone-project-btn"
        class="primary"
        :disabled="!newProjectName || !currentWorkspace"
        @click="onCloneProject"
        data-cy="clone-dialog-clone-btn"
      >
        Clone
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script lang="ts">
import { mapActions, mapState } from 'pinia'
import { defineComponent } from 'vue'

import { useDialogStore } from '@/modules/dialog/store'
import { useFormStore } from '@/modules/form/store'
import { useProjectStore } from '@/modules/project/store'
import { CloneProjectParams } from '@/modules/project/types'
import { useUserStore } from '@/modules/user/store'

export default defineComponent({
  name: 'clone-dialog-template',
  props: {
    namespace: String,
    project: String
  },
  data() {
    return {
      newProjectName: ''
    }
  },
  computed: {
    ...mapState(useUserStore, ['currentWorkspace'])
  },
  created() {
    this.newProjectName = this.project
  },
  beforeDestroy() {
    this.clearErrors({
      componentId: this.merginComponentUuid,
      keepNotification: true
    })
  },
  methods: {
    ...mapActions(useDialogStore, ['close']),
    ...mapActions(useFormStore, ['clearErrors', 'handleError']),
    ...mapActions(useProjectStore, ['cloneProject']),

    successCloneCallback() {
      this.close()
    },

    onCloneProject() {
      this.clearErrors({ componentId: this.merginComponentUuid })
      const data: CloneProjectParams = {
        project: this.newProjectName,
        namespace: this.namespace,
        merginComponentUuid: this.merginComponentUuid
      }
      this.$emit(
        'on-clone-project',
        this.project,
        this.namespace,
        data,
        this.successCloneCallback
      )
    }
  }
})
</script>
