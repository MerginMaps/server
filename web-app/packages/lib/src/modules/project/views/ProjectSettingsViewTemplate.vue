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
              <template v-if="project.access.public"
                >This is public project</template
              >
              <template v-else>This is private project</template>
            </template>

            <template #description>
              <template v-if="project.access.public">
                Hide this project from everyone
              </template>
              <template v-else>Make this project visible to anyone.</template>
            </template>

            <template #action>
              <div class="flex-shrink-0">
                <PButton
                  @click="confirmPublicPrivate()"
                  severity="secondary"
                  data-cy="settings-public-btn"
                  :label="
                    project.access.public ? 'Make private' : 'Make public'
                  "
                />
              </div>
            </template>
          </app-settings-item>
          <slot name="operations"></slot>
          <app-settings-item>
            <template #title>Delete project</template>
            <template #description>All data will be lost</template>
            <template #action
              ><div class="flex-shrink-0">
                <PButton
                  @click="confirmDelete"
                  severity="danger"
                  data-cy="settings-delete-btn"
                  label="Delete project"
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
    ...mapActions(useProjectStore, ['deleteProject', 'updateProjectAccess']),
    ...mapActions(useDialogStore, { showDialog: 'show' }),
    togglePublicPrivate() {
      this.updateProjectAccess({
        projectId: this.project.id,
        data: {
          public: !this.project.access.public
        }
      })
    },
    confirmDelete() {
      const props: ConfirmDialogProps = {
        text: `Are you sure to delete project?`,
        description: 'All files will be lost. Type in project name to confirm:',
        hint: `${this.projectName}`,
        severity: 'danger',
        confirmText: 'Delete',
        confirmField: {
          label: 'Project name',
          expected: this.projectName
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
          dialog: { header: 'Confirm delete project' }
        }
      })
    },
    confirmPublicPrivate() {
      const props: ConfirmDialogProps = {
        text: `Do you really want to make this project ${
          this.project?.access.public ? 'private' : 'public'
        }?`,
        confirmText: 'Yes',
        cancelText: 'No',
        description: this.project?.access.public
          ? 'Once you make your project private it can not be accessed by the community.'
          : 'Once you make your project public it can be accessed by the community.'
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
              ? 'Private project'
              : 'Public project'
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
