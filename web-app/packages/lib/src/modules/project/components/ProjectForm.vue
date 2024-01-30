<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <div class="py-4">
    <div class="mb-4">
      <span class="flex p-float-label w-full p-input-filled">
        <PInputText
          autofocus
          id="name"
          v-model="name"
          type="text"
          :class="{ 'p-invalid': errors.detail }"
          aria-describedby="text-error"
          data-cy="project-form-name"
          class="flex-grow-1"
        />
        <label for="name">Project name</label>
        <small class="p-error" id="text-error">{{
          errors.detail || '&nbsp;'
        }}</small>
      </span>
    </div>

    <tip-message class="mb-6">
      ><template #description
        >A good candidate for a project name is name of the location or purpose
        of the field survey.</template
      ></tip-message
    >

    <div
      class="flex flex-column lg:flex-row justify-content-between align-items-center"
    >
      <PButton
        severity="secondary"
        @click="close"
        class="flex w-12 mb-2 lg:mb-0 lg:mr-2 lg:w-6 justify-content-center"
        >Cancel</PButton
      >

      <PButton
        id="create-project-btn"
        :disabled="!name"
        @click="create"
        data-cy="project-form-create-btn"
        class="flex w-12 lg:w-6 justify-content-center"
      >
        Create project
      </PButton>
    </div>
  </div>
</template>

<script lang="ts">
import { mapActions, mapState } from 'pinia'
import { defineComponent } from 'vue'

import { TipMessage } from '@/common/components'
import { useDialogStore } from '@/modules/dialog/store'
import { useFormStore } from '@/modules/form/store'
import { useProjectStore } from '@/modules/project/store'

export default defineComponent({
  name: 'new-project-form',
  components: {
    TipMessage
  },
  data() {
    return {
      name: ''
    }
  },
  computed: {
    ...mapState(useProjectStore, ['currentNamespace']),
    ...mapState(useFormStore, ['getErrorByComponentId']),
    errors() {
      return this.getErrorByComponentId(this.merginComponentUuid) ?? {}
    }
  },
  beforeDestroy() {
    this.clearErrors({
      componentId: this.merginComponentUuid,
      keepNotification: true
    })
  },
  methods: {
    ...mapActions(useDialogStore, ['close']),
    ...mapActions(useFormStore, ['clearErrors']),
    ...mapActions(useProjectStore, ['createProject']),

    async create() {
      // TODO: add types
      const dialogData = { componentId: this.merginComponentUuid }
      await this.clearErrors(dialogData)
      try {
        const data = {
          name: this.name.trim(),
          public: false
        }
        await this.createProject({
          data,
          namespace: this.currentNamespace
        })
        await this.close()
        this.$emit('success')
      } catch (err) {
        this.$emit('error', err, dialogData)
      }
    },
    beforeDestroy() {
      this.clearErrors({
        componentId: this.merginComponentUuid,
        keepNotification: true
      })
    }
  }
})
</script>
