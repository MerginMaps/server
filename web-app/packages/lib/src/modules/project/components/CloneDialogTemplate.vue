<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <div class="flex flex-column gap-4 pb-4">
    <span class="flex p-float-label w-ful p-input-filled">
      <PInputText
        autofocus
        id="name"
        v-model="newProjectName"
        type="text"
        aria-describedby="text-error"
        data-cy="clone-dialog-project-name"
        class="flex-grow-1"
      />
      <label for="name">Project name</label>
    </span>
    <!-- Dynamic items to pass other inputs -->
    <slot name="dynamic-items"></slot>

    <!-- Footer -->
    <div
      class="flex flex-column lg:flex-row justify-content-between align-items-center pt-3"
    >
      <PButton
        severity="secondary"
        @click="close"
        class="flex w-12 mb-2 lg:mb-0 lg:mr-2 lg:w-6 justify-content-center"
        data-cy="clone-dialog-close-btn"
        >Cancel</PButton
      >

      <PButton
        id="clone-project-btn"
        :disabled="!newProjectName || !currentWorkspace"
        @click="onCloneProject"
        data-cy="project-form-create-btn"
        class="flex w-12 lg:w-6 justify-content-center"
      >
        Clone project
      </PButton>
    </div>
  </div>
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
  beforeUnmount() {
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
