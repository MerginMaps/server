<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <v-card v-on:keyup.enter="createProject">
    <v-card-title>
      <span class="text-h5">New project</span>
    </v-card-title>
    <v-card-text>
      <p class="text-xs-center red--text" v-text="error" />
      <v-text-field
        autofocus
        label="name"
        v-model="name"
        data-cy="project-form-name"
      />
    </v-card-text>
    <v-card-actions>
      <v-spacer />
      <v-btn @click="close" class="black--text"> Close</v-btn>
      <v-btn
        id="create-project-btn"
        class="primary"
        :disabled="!name"
        @click="createProject"
        data-cy="project-form-create-btn"
      >
        Create
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script lang="ts">
import { defineComponent } from 'vue'
import { mapActions, mapState } from 'vuex'

export default defineComponent({
  name: 'new-project',
  data() {
    return {
      name: '',
      error: null
    }
  },
  computed: {
    ...mapState('projectModule', ['currentNamespace'])
  },
  beforeDestroy() {
    this.clearErrors({
      componentId: this.merginComponentUuid,
      keepNotification: true
    })
  },
  methods: {
    ...mapActions('dialogModule', ['close']),
    ...mapActions('formModule', ['clearErrors']),
    ...mapActions('projectModule', { createProjectAction: 'createProject' }),

    async createProject() {
      await this.clearErrors({ componentId: this.merginComponentUuid })
      try {
        const data = {
          name: this.name.trim(),
          public: false
        } as any
        await this.createProjectAction({
          data,
          namespace: this.currentNamespace
        })
        await this.close()
      } catch (_error) {
        // do not close
      }
    }
  }
})
</script>
