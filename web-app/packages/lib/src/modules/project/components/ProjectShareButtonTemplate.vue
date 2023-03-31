<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <action-button :disabled="false" @click="onShareProject" v-if="loggedUser">
    <template #icon>
      <plus-icon />
    </template>
    Share
  </action-button>
</template>

<script lang="ts">
import Vue from 'vue'
import { PlusIcon } from 'vue-tabler-icons'
import { mapActions, mapState } from 'vuex'

import ActionButton from '@/common/components/ActionButton.vue'
import ProjectShareDialog from '@/modules/project/components/ProjectShareDialog.vue'

export default Vue.extend({
  props: {
    allowInvite: Boolean
  },
  components: { ActionButton, PlusIcon },
  computed: {
    ...mapState('userModule', ['loggedUser'])
  },
  methods: {
    ...mapActions('dialogModule', ['show']),

    onShareProject() {
      const dialogProps = { allowInvite: this.allowInvite }
      const listeners = {
        ...(this.$listeners['on-invite']
          ? { 'on-invite': this.$listeners['on-invite'] }
          : {})
      }
      const dialog = {
        maxWidth: 600,
        persistent: true
      }
      this.show({
        component: ProjectShareDialog,
        params: {
          props: dialogProps,
          listeners,
          dialog
        }
      })
    }
  }
})
</script>

<style lang="scss" scoped></style>
