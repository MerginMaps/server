<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <ConfirmDialog
    :text="t('DoYouReallyWishToCloseYourAccount')"
    :description="
      t(
        'ThisActionWillDeleteYourMerginMapsAccountIfYouAreAWorkspaceOwnerYouNeedToTransferTheOwnershipToSomebodyElseOrCloseTheWorkspace'
      )
    "
    :cancelText="t('No')"
    :confirmText="t('Yes')"
    :hint="username"
    :confirmField="{
      label: t('Username'),
      expected: username,
      placeholder: t('Username')
    }"
    severity="danger"
    @confirm="confirm"
  />
</template>

<script setup lang="ts">
import returnTranslation from '@/../../lang/translate'
import { DeleteAccountConfirmProps } from '@/modules'
import ConfirmDialog from '@/modules/dialog/components/ConfirmDialog.vue'

defineProps<DeleteAccountConfirmProps>()
const emit = defineEmits(['confirm'])
const t = (key: string) => returnTranslation(import.meta.env.VITE_LANG, key)

function confirm() {
  emit('confirm')
}
</script>
