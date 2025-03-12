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
  />
</template>

<script setup lang="ts">
import { DeleteAccountConfirmProps } from '@/modules'
import ConfirmDialog from '@/modules/dialog/components/ConfirmDialog.vue'

defineProps<DeleteAccountConfirmProps>()
const emit = defineEmits(['confirm'])

function confirm() {
  emit('confirm')
}
</script>
