<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <label class="flex align-items-center" :for="'for'"
    ><slot name="label"></slot>&nbsp;
    <i
      class="ti ti-info-circle-filled cursor-pointer text-color-medium-green hover:text-color paragraph-p4"
      :style="{ color: 'var(--medium-green-color)' }"
      v-tooltip="{
        value: tooltip,
        escape: false
      }"
  /></label>
</template>

<script lang="ts" setup>
import returnTranslation from '@/../../lang/translate'

defineProps<{ for: string }>()

const t = (key: string) => returnTranslation(import.meta.env.VITE_LANG, key)

const tooltip = `
  <ul>
    <li>${t('PasswordMustBeAtLeastCharactersLong')}</li>
    <li>${t(
      'PasswordMustContainAtLeastCharacterCategoriesAmongTheFollowing'
    )}</li>
    <ul>
      <li>${t('LowercaseCharactersAZ')}</li>
      <li>${t('UppercaseCharactersAZ')}</li>
      <li>${t('Digits09')}</li>
      <li>${t('SpecialCharacters')}</li>
    </ul>
  </ul>
`
</script>
