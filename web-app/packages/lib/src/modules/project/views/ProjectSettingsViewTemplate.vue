<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <div>
    <app-container v-if="showAccessRequests && accessRequestsCount > 0">
      <app-section
        ><template #title
          >Requests
          <span class="text-color-secondary"
            >({{ accessRequestsCount }})</span
          ></template
        ><project-access-requests
      /></app-section>
    </app-container>
    <slot
      name="permissions"
      :settings="settings"
      :key-prop="key"
      :save-project="saveProject"
    ></slot>

    <app-container>
      <app-section-banner>
        <template #title>Advanced</template>
        <div
          :class="[
            'flex flex-column align-items-start text-sm py-2',
            'row-gap-2',
            'md:align-items-center md:flex-row'
          ]"
        >
          <div class="flex-grow-1">
            <template v-if="settings.access.public">
              <p class="font-semibold py-1 m-0">This is public project</p>
              <span class="text-xs opacity-80"
                >Hide this project from everyone.</span
              >
            </template>
            <template v-else>
              <p class="font-semibold py-1 m-0">This is private project</p>
              <span class="text-xs opacity-80"
                >Make this project visible to anyone.</span
              >
            </template>
          </div>
          <div class="flex-shrink-0">
            <PButton
              @click="confirmPublicPrivate()"
              severity="secondary"
              data-cy="settings-public-btn"
            >
              <template v-if="settings.access.public">Make private</template>
              <template v-else>Make public</template>
            </PButton>
          </div>
        </div>
        <div
          :class="[
            'flex flex-column align-items-start text-sm py-2',
            'row-gap-2',
            'md:align-items-center md:flex-row'
          ]"
          v-if="$slots.operations"
        >
          <slot name="operations"></slot>
        </div>
        <div
          :class="[
            'flex flex-column align-items-start text-sm py-2',
            'row-gap-2',
            'md:align-items-center md:flex-row'
          ]"
          v-if="project && project.permissions && project.permissions.delete"
        >
          <div class="flex-grow-1">
            <p class="font-semibold m-0 py-1">Delete project</p>
            <span class="text-xs opacity-80">All data will be lost</span>
          </div>
          <div class="flex-shrink-0">
            <PButton
              @click="confirmDelete"
              severity="danger"
              data-cy="settings-delete-btn"
            >
              Delete project</PButton
            >
          </div>
        </div>
      </app-section-banner>
    </app-container>
  </div>
</template>

<script lang="ts">
import debounce from 'lodash/debounce'
import { mapActions, mapState } from 'pinia'
import { PropType, defineComponent } from 'vue'

import AppContainer from '@/common/components/AppContainer.vue'
import AppSection from '@/common/components/AppSection.vue'
import AppSectionBanner from '@/common/components/AppSectionBanner.vue'
import { getErrorMessage } from '@/common/error_utils'
import { ConfirmDialogProps, ProjectAccess } from '@/modules'
import ConfirmDialog from '@/modules/dialog/components/ConfirmDialog.vue'
import { useDialogStore } from '@/modules/dialog/store'
import { useNotificationStore } from '@/modules/notification/store'
import ProjectAccessRequests from '@/modules/project/components/ProjectAccessRequests.vue'
import { useProjectStore } from '@/modules/project/store'
import { useUserStore } from '@/modules/user/store'

export default defineComponent({
  name: 'ProjectSettingsViewTemplate',
  components: {
    ProjectAccessRequests,
    AppContainer,
    AppSection,
    AppSectionBanner
  },
  props: {
    namespace: String,
    projectName: String,
    asAdmin: {
      type: Boolean,
      default: false
    },
    showSettings: Boolean,
    showAccessRequests: {
      type: Boolean as PropType<boolean>,
      default: false
    }
  },
  data() {
    return {
      settings: {} as { access?: ProjectAccess },
      key: 0
    }
  },
  computed: {
    ...mapState(useUserStore, ['loggedUser']),
    ...mapState(useProjectStore, ['project', 'accessRequestsCount'])
  },
  watch: {
    project: {
      immediate: true,
      handler(project) {
        if (
          JSON.stringify(this.settings.access) !==
          JSON.stringify(this.project?.access)
        ) {
          this.settings = {
            access: JSON.parse(JSON.stringify(project.access))
          }
        }
        this.key++
      }
    }
  },
  created() {
    if (!this.showSettings) {
      this.$router.push('/projects')
    }
    this.settings = {
      access: JSON.parse(JSON.stringify(this.project.access))
    }
  },
  methods: {
    ...mapActions(useProjectStore, ['deleteProject', 'saveProjectSettings']),
    ...mapActions(useDialogStore, { showDialog: 'show' }),
    ...mapActions(useNotificationStore, ['error']),

    saveProject(newSettingsAccessValues) {
      const newSettings = {
        ...this.settings,
        access: { ...this.settings.access, ...newSettingsAccessValues }
      }
      this.settings.access.readersnames = newSettings.access.readersnames
      this.settings.access.ownersnames = newSettings.access.ownersnames
      this.settings.access.writersnames = newSettings.access.writersnames
      this.saveSettings(newSettings)
    },
    saveSettings: debounce(function (newSettings) {
      try {
        this.saveProjectSettings({
          namespace: this.namespace,
          newSettings,
          projectName: this.projectName
        })
      } catch (err) {
        this.error({
          text: getErrorMessage(err, 'Failed to save project settings')
        })
      }
    }, 2000),
    togglePublicPrivate() {
      this.settings.access.public = !this.settings.access.public
      this.saveSettings(this.settings)
    },
    confirmDelete() {
      const props: ConfirmDialogProps = {
        text: `Are you sure to delete project: ${this.projectName}?`,
        description: 'All files will be lost. Type in project name to confirm:',
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
          this.settings.access.public ? 'private' : 'public'
        }?`,
        confirmText: 'Yes',
        description: this.settings.access.public
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
            header: this.settings.access.public
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
