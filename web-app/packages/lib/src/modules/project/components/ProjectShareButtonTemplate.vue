<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <PButton
    @click="onShareProject"
    v-if="loggedUser"
    icon="ti ti-send"
    label="Share"
    class="mr-2"
  />
</template>

<script lang="ts">
import { mapActions, mapState } from 'pinia'
import { defineComponent } from 'vue'

import { useDialogStore } from '@/modules/dialog/store'
import ProjectShareDialog from '@/modules/project/components/ProjectShareDialog.vue'
import { useUserStore } from '@/modules/user/store'

export default defineComponent({
  props: {
    allowInvite: Boolean
  },
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
        persistent: true,
        header: 'Share project'
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
