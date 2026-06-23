<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <div>
    <app-container>
      <app-section class="pt-4">
        <app-settings>
          <app-settings-item>
            <template #title>
              <template v-if="project.access.public">{{
                t('ThisIsPublicProject')
              }}</template>
              <template v-else>{{ t('ThisIsPrivateProject') }}</template>
            </template>

            <template #description>
              <template v-if="project.access.public">
                {{ t('HideThisProjectFromEveryone') }}
              </template>
              <template v-else>{{
                t('MakeThisProjectVisibleToAnyone')
              }}</template>
            </template>

            <template #action>
              <div class="flex-shrink-0">
                <PButton
                  @click="confirmPublicPrivate()"
                  severity="secondary"
                  data-cy="settings-public-btn"
                  :label="
                    project.access.public ? t('MakePrivate') : t('MakePublic')
                  "
                />
              </div>
            </template>
          </app-settings-item>
          <slot name="operations"></slot>
          <app-settings-item>
            <template #title>{{ t('DeleteProject') }}</template>
            <template #description>{{ t('AllDataWillBeLost') }}</template>
            <template #action
              ><div class="flex-shrink-0">
                <PButton
                  @click="confirmDelete"
                  severity="danger"
                  data-cy="settings-delete-btn"
                  :label="t('DeleteProject')"
                /></div
            ></template>
          </app-settings-item>
        </app-settings>
      </app-section>
    </app-container>
  </div>
</template>

<script lang="ts">
import { mapActions, mapState } from 'pinia'
import { PropType, defineComponent } from 'vue'

import returnTranslation from '@/../../lang/translate'
import AppSettings from '@/common/components/app-settings/AppSettings.vue'
import AppSettingsItem from '@/common/components/app-settings/AppSettingsItem.vue'
import AppContainer from '@/common/components/AppContainer.vue'
import AppSection from '@/common/components/AppSection.vue'
import { ConfirmDialogProps } from '@/modules'
import ConfirmDialog from '@/modules/dialog/components/ConfirmDialog.vue'
import { useDialogStore } from '@/modules/dialog/store'
import { useProjectStore } from '@/modules/project/store'

export default defineComponent({
  name: 'ProjectSettingsViewTemplate',
  components: {
    AppContainer,
    AppSection,
    AppSettings,
    AppSettingsItem
  },
  props: {
    projectName: String,
    showSettings: Boolean,
    showAccessRequests: {
      type: Boolean as PropType<boolean>,
      default: false
    }
  },
  computed: {
    ...mapState(useProjectStore, ['project', 'accessRequestsCount'])
  },
  created() {
    if (!this.showSettings) {
      this.$router.push('/projects')
    }
  },
  methods: {
    ...mapActions(useProjectStore, ['deleteProject', 'updatePublicFlag']),
    ...mapActions(useDialogStore, { showDialog: 'show' }),
    t(key: string) {
      return returnTranslation(import.meta.env.VITE_LANG, key)
    },
    togglePublicPrivate() {
      this.updatePublicFlag({
        projectId: this.project.id,
        data: {
          public: !this.project.access.public
        }
      })
    },
    confirmDelete() {
      const props: ConfirmDialogProps = {
        text: this.t('AreYouSureToDeleteProject'),
        description: this.t('AllFilesWillBeLostTypeInProjectNameToConfirm'),
        hint: `${this.projectName}`,
        severity: 'danger',
        confirmText: this.t('Delete'),
        confirmField: {
          label: this.t('ProjectName'),
          expected: this.projectName,
          placeholder: this.t('TypeInProjectNameToConfirmDeletion')
        }
      }
      const listeners = {
        confirm: () => this.onDeleteProject()
      }
      this.showDialog({
        component: ConfirmDialog,
        params: {
          props,
          listeners,
          dialog: { header: this.t('ConfirmDeleteProject') }
        }
      })
    },
    confirmPublicPrivate() {
      const props: ConfirmDialogProps = {
        text: `Do you really want to make this project ${
          this.project?.access.public ? this.t('Private') : this.t('Public')
        }?`,
        confirmText: this.t('Yes'),
        cancelText: this.t('No'),
        description: this.project?.access.public
          ? this.t(
              'OnceYouMakeYourProjectPrivateItCanNotBeAccessedByTheCommunity'
            )
          : this.t('OnceYouMakeYourProjectPublicItCanBeAccessedByTheCommunity')
      }
      const listeners = {
        confirm: () => this.togglePublicPrivate()
      }
      this.showDialog({
        component: ConfirmDialog,
        params: {
          props,
          listeners,
          dialog: {
            header: this.project?.access.public
              ? this.t('PrivateProject')
              : this.t('PublicProject')
          }
        }
      })
    },
    onDeleteProject() {
      this.deleteProject({
        projectId: this.project.id
      })
    }
  }
})
</script>

<style lang="scss" scoped></style>
