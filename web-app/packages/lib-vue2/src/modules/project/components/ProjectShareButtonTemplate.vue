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
import { mapActions, mapState } from 'pinia'
import { defineComponent } from 'vue'
import { PlusIcon } from 'vue-tabler-icons'

import ActionButton from '@/common/components/ActionButton.vue'
import { useDialogStore } from '@/modules/dialog/store'
import ProjectShareDialog from '@/modules/project/components/ProjectShareDialog.vue'
import { useUserStore } from '@/modules/user/store'

export default defineComponent({
  props: {
    allowInvite: Boolean
  },
  components: { ActionButton, PlusIcon },
  computed: {
    ...mapState(useUserStore, ['loggedUser'])
  },
  methods: {
    ...mapActions(useDialogStore, ['show']),

    onShareProject() {
      const dialogProps = { allowInvite: this.allowInvite }
      const listeners = {
        ...(this.$attrs['on-invite']
          ? { 'on-invite': this.$attrs['on-invite'] }
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
