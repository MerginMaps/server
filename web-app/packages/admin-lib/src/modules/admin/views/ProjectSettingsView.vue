<template>
  <app-container>
    <app-section>
      <template #title>{{ $t('Advanced') }}</template>
      <app-settings :items="settingsItems">
        <template #publicProject>
          <div class="flex-shrink-0 paragraph-p1">
            <PInputSwitch :model-value="project?.access?.public" disabled />
          </div>
        </template>
        <template #deleteProject>
          <div class="flex-shrink-0">
            <PButton
              @click="confirmDelete"
              severity="danger"
              data-cy="project-delete-btn"
              :label="$t('DeleteProject')"
            />
          </div>
        </template>
      </app-settings>
    </app-section>
  </app-container>
</template>

<script lang="ts" setup>
import {
  AppContainer,
  AppSection,
  AppSettings,
  AppSettingsItemConfig,
  ConfirmDialog,
  ConfirmDialogProps,
  useDialogStore,
  useProjectStore
} from '@mergin/lib'
import { computed } from 'vue'

import returnTranslation from '@/../../lang/translate'
import { useAdminStore } from '@/modules/admin/store'

const projectStore = useProjectStore()
const dialogStore = useDialogStore()
const adminStore = useAdminStore()
const t = (key: string) => returnTranslation(import.meta.env.VITE_LANG, key)

const project = computed(() => projectStore.project)

const settingsItems = computed<AppSettingsItemConfig[]>(() => [
  {
    key: 'publicProject',
    title: t('PublicProject'),
    description: t('TheProjectWillBeVisibleToEveryoneIfItIsMarkedAsPublic')
  },
  {
    key: 'deleteProject',
    title: t('DeleteProject'),
    description: t(
      'DeletingThisProjectWillRemoveItAndAllItsDataThisActionCannotBeUndone'
    )
  }
])

const confirmDelete = () => {
  const props: ConfirmDialogProps = {
    text: t('AreYouSureYouWantToPermanentlyDeleteThisProject'),
    description: t(
      'DeletingThisProjectWillRemoveItAndAllItsDataThisActionCannotBeUndoneTypeInProjectNameToConfirm'
    ),
    hint: project.value.name,
    confirmText: t('DeletePermanently'),
    confirmField: {
      label: t('ProjectName'),
      expected: project.value.name
    },
    severity: 'danger'
  }
  const listeners = {
    confirm: async () =>
      await adminStore.deleteProject({ projectId: project.value.id })
  }
  dialogStore.show({
    component: ConfirmDialog,
    params: { props, listeners, dialog: { header: t('DeleteProject') } }
  })
}
</script>
