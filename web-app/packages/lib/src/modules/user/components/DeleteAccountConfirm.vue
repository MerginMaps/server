<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <ConfirmDialog
    text="Do you really wish to close your account?"
    description="This action will delete your Mergin Maps account. If you are a workspace owner, you need to transfer the ownership to somebody else or close the workspace."
    cancelText="No"
    confirmText="Yes"
    :hint="username"
    :confirmField="{
      label: 'Username',
      expected: username
    }"
    severity="danger"
    @confirm="confirm"
  >
    <TipMessage>
      <template #image
        ><img wdth="50" height="50" src="@/assets/exclamation.svg"
      /></template>
      <template #title>Please note</template>
      <template #description
        >In order to delete your account, enter your username in the field above
        and click Yes.</template
      >
    </TipMessage>
  </ConfirmDialog>
</template>

<script setup lang="ts">
import TipMessage from '@/common/components/TipMessage.vue'
import { DeleteAccountConfirmProps } from '@/modules'
import ConfirmDialog from '@/modules/dialog/components/ConfirmDialog.vue'

defineProps<DeleteAccountConfirmProps>()
const emit = defineEmits(['confirm'])

function confirm() {
  emit('confirm')
}
</script>
