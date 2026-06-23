<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <admin-layout>
    <app-container>
      <app-section ground>
        <template #header
          ><h1 class="headline-h3">{{ $t('Settings') }}</h1></template
        >
      </app-section>
    </app-container>

    <app-container>
      <app-section>
        <template #title>{{ $t('Advanced') }}</template>
        <app-settings :items="resolvedSettingsItems">
          <template #items-start><slot /></template>

          <template #checkForUpdates
            ><PInputSwitch
              :modelValue="adminStore.checkForUpdates"
              @change="switchCheckForUpdates"
          /></template>
          <template #downloadReport
            ><PButton
              severity="secondary"
              @click="downloadReport"
              :label="$t('Download')"
          /></template>
        </app-settings>
      </app-section>
    </app-container>
  </admin-layout>
</template>

<script setup lang="ts">
import {
  AppContainer,
  AppSection,
  AppSettings,
  AppSettingsItemConfig,
  useDialogStore
} from '@mergin/lib'
import { computed } from 'vue'

import ReportDownloadDialog from '../components/ReportDownloadDialog.vue'
import { useAdminStore } from '../store'

import returnTranslation from '@/../../lang/translate'
import AdminLayout from '@/modules/admin/components/AdminLayout.vue'

const t = (key: string) => returnTranslation(import.meta.env.VITE_LANG, key)

const props = defineProps<{ settingsItems?: AppSettingsItemConfig[] }>()

const defaultSettingsItems = computed<AppSettingsItemConfig[]>(() => [
  {
    title: t('CheckForUpdates'),
    description: t('LetMerginMapsAutomaticallyCheckForNewUpdates'),
    key: 'checkForUpdates'
  },
  {
    title: t('ServerUsageReport'),
    description: t('DownloadUsageStatisticsForYourServerDeployment'),
    key: 'downloadReport'
  }
])

const resolvedSettingsItems = computed(
  () => props.settingsItems ?? defaultSettingsItems.value
)

const adminStore = useAdminStore()
const dialogStore = useDialogStore()

function switchCheckForUpdates() {
  const value = !adminStore.checkForUpdates
  adminStore.setCheckUpdatesToCookies({ value })
}

function downloadReport() {
  dialogStore.show({
    component: ReportDownloadDialog,
    params: {
      dialog: { header: t('DownloadReport') }
    }
  })
}
</script>

<style lang="scss" scoped></style>
