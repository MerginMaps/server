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
          <span class="opacity-80">({{ accessRequestsCount }})</span></template
        ><project-access-requests
      /></app-section>
    </app-container>
    <app-container>
      <app-section>
        <div class="flex flex-column row-gap-3 text-sm p-4">
          <div
            :class="[
              'flex flex-column align-items-start',
              'row-gap-2',
              'md:align-items-center md:flex-row'
            ]"
          >
            <div class="flex-grow-1">
              <template v-if="project.access.public">
                <p class="font-semibold my-2">This is public project</p>
                <span class="text-xs opacity-80"
                  >Hide this project from everyone.</span
                >
              </template>
              <template v-else>
                <p class="font-semibold my-2">This is private project</p>
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
                :label="project.access.public ? 'Make private' : 'Make public'"
              />
            </div>
          </div>
          <div
            :class="[
              'flex flex-column align-items-start',
              'row-gap-2',
              'md:align-items-center md:flex-row'
            ]"
            v-if="$slots.operations"
          >
            <slot name="operations"></slot>
          </div>
          <div
            :class="[
              'flex flex-column align-items-start',
              'row-gap-2',
              'md:align-items-center md:flex-row'
            ]"
            v-if="project && project.permissions && project.permissions.delete"
          >
            <div class="flex-grow-1">
              <p class="font-semibold my-2">Delete project</p>
              <span class="text-xs opacity-80">All data will be lost</span>
            </div>
            <div class="flex-shrink-0">
              <PButton
                @click="confirmDelete"
                severity="danger"
                data-cy="settings-delete-btn"
                label="Delete project"
              />
            </div>
          </div>
        </div>
      </app-section>
    </app-container>
  </div>
</template>

<script lang="ts">
import { mapActions, mapState } from 'pinia'
import { PropType, defineComponent } from 'vue'

import AppContainer from '@/common/components/AppContainer.vue'
import AppSection from '@/common/components/AppSection.vue'
import { ConfirmDialogProps } from '@/modules'
import ConfirmDialog from '@/modules/dialog/components/ConfirmDialog.vue'
import { useDialogStore } from '@/modules/dialog/store'
import ProjectAccessRequests from '@/modules/project/components/ProjectAccessRequests.vue'
import { useProjectStore } from '@/modules/project/store'

export default defineComponent({
  name: 'ProjectSettingsViewTemplate',
  components: {
    ProjectAccessRequests,
    AppContainer,
    AppSection
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
          this.project?.access.public ? 'private' : 'public'
        }?`,
        confirmText: 'Yes',
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
