<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <v-layout class="settings column">
    <slot
      name="permissions"
      :settings="settings"
      :key-prop="key"
      :save-project="saveProject"
    ></slot>
    <project-access-requests />
    <v-layout class="public-private-zone">
      <v-container>
        <v-row>
          <v-col>
            <span class="private-public-text" v-if="settings.access.public">
              <b>This is public project</b><br />
              <span class="description-text"
                >Hide this project from everyone.</span
              >
            </span>
            <span class="private-public-text" v-else>
              <b>This is private project</b><br />
              <span class="description-text"
                >Make this project visible to anyone.</span
              >
            </span>
          </v-col>
          <v-col>
            <v-btn
              @click="confirmPublicPrivate()"
              class="private-public-btn"
              outlined
            >
              <span v-if="settings.access.public">Make private</span>
              <span v-else>Make public</span>
            </v-btn>
          </v-col>
        </v-row>
        <slot name="operations"></slot>
        <v-row
          v-if="project && project.permissions && project.permissions.delete"
        >
          <v-col>
            <span class="private-public-text">
              <b>Delete project</b><br />
              <span class="description-text">All data will be lost</span></span
            >
          </v-col>
          <v-col self-align="end">
            <v-btn @click="confirmDelete" class="private-public-btn" outlined>
              <span>Delete</span>
            </v-btn>
          </v-col>
        </v-row>
      </v-container>
    </v-layout>
  </v-layout>
</template>

<script lang="ts">
import debounce from 'lodash/debounce'
import { mapActions, mapState } from 'pinia'
import { defineComponent } from 'vue'

import { getErrorMessage } from '@/common/error_utils'
import ConfirmDialog from '@/modules/dialog/components/ConfirmDialog.vue'
import { useDialogStore } from '@/modules/dialog/store'
import { useNotificationStore } from '@/modules/notification/store'
import ProjectAccessRequests from '@/modules/project/components/ProjectAccessRequests.vue'
import { useProjectStore } from '@/modules/project/store'
import { useUserStore } from '@/modules/user/store'

export default defineComponent({
  name: 'ProjectSettingsViewTemplate',
  components: {
    ProjectAccessRequests
  },
  props: {
    namespace: String,
    projectName: String,
    asAdmin: {
      type: Boolean,
      default: false
    },
    showSettings: Boolean
  },
  data() {
    return {
      settings: {},
      key: 0
    }
  },
  computed: {
    ...mapState(useUserStore, ['loggedUser']),
    ...mapState(useProjectStore, ['project'])
  },
  watch: {
    project: {
      immediate: true,
      handler(project) {
        if (
          JSON.stringify(this.settings.access) !==
          JSON.stringify(this.project.access)
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
    ...mapActions(useDialogStore, ['show']),
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
    },
    confirmDelete() {
      const props = {
        text: `Are you sure to delete project: ${this.projectName}? All files will be lost. <br> <br> Type in project name to confirm:`,
        confirmText: 'Delete',
        confirmField: {
          label: 'Project name',
          expected: this.projectName
        }
      }
      const listeners = {
        confirm: () => this.onDeleteProject()
      }
      this.show({
        component: ConfirmDialog,
        params: { props, listeners, dialog: { maxWidth: 500 } }
      })
    },
    confirmPublicPrivate() {
      const props = {
        text: `Do you really want to make this project ${
          this.settings.access.public ? 'private' : 'public'
        }?`,
        confirmText: 'Yes'
      }
      const listeners = {
        confirm: () => this.togglePublicPrivate()
      }
      this.show({
        component: ConfirmDialog,
        params: { props, listeners, dialog: { maxWidth: 500 } }
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

<style lang="scss" scoped>
@use '@/sass/project';

.settings {
  display: flex;
  flex-direction: column;
  flex: 1 0 auto;
}

.actions {
  flex: 0 0 auto;
}
</style>
