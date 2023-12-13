<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <div>
    <template v-if="project">
      <app-container class="flex justify-content-end xl:pb-1 -mb-6">
        <!-- Z indexes based on minus margin, its not possible to add additional buttons to tab view -->
        <div class="relative z-1">
          <!-- Toolbar -->
          <portal-target name="project-toolbar" class="layout row shrink" />
          <slot name="shareButton">
            <project-share-button />
          </slot>
          <action-button
            @click="downloadArchive({ url: downloadUrl })"
            data-cy="project-download-btn"
          >
            <template #icon>
              <download-icon />
            </template>
            Download
          </action-button>
          <action-button
            @click="cloneDialog"
            v-if="canCloneProject"
            data-cy="project-clone-btn"
          >
            <template #icon>
              <copy-icon />
            </template>
            Clone
          </action-button>
          <action-button
            @click="unsubscribeDialog"
            data-cy="project-leave-btn"
            v-if="canLeaveProject"
          >
            <template #icon>
              <square-minus-icon />
            </template>
            Leave project
          </action-button>
        </div>
      </app-container>

      <PTabView
        :active-index="activeTabIndex"
        @tab-click="(e) => tabClick(e.index)"
        lazy
        :pt="{
          root: {
            class: 'relative z-auto'
          },
          nav: {
            style: {
              backgroundColor: 'transparent',
              maxWidth: '1120px'
            },
            class: 'mx-auto border-transparent'
          },
          panelContainer: {
            style: {
              backgroundColor: 'transparent'
            },
            class: 'p-0'
          }
        }"
      >
        <PTabPanel header="Files" :pt="ptHeaderAction">
          <router-view v-if="project" class="content-container" />
        </PTabPanel>
        <slot name="map.tab" :ptHeaderAction="ptHeaderAction" />
        <PTabPanel
          v-if="tabs.some((item) => item.route === `project-versions`)"
          header="History"
          :pt="ptHeaderAction"
          ><router-view v-if="project" class="content-container" />
        </PTabPanel>
        <PTabPanel
          v-if="tabs.some((item) => item.route === `project-settings`)"
          header="Settings"
          :pt="ptHeaderAction"
          ><router-view v-if="project" class="content-container" />
        </PTabPanel>
      </PTabView>
    </template>
    <app-section v-else-if="fetchProjectsResponseStatus === 403">
      <v-layout
        class="public-private-zone"
        style="padding-top: 25px; padding-left: 25px"
      >
        <v-btn id="request-access-btn" @click="createAccessRequest"
          >Request access
        </v-btn>
        <span class="private-public-text">
          <b>This is a private project</b><br />
          You don't have permissions to access this project.
        </span>
      </v-layout>
    </app-section>
    <app-section v-else-if="fetchProjectsResponseStatus === 404">
      <span
        class="private-public-text"
        style="padding-top: 25px; padding-left: 25px"
      >
        <b>Project not found</b><br />
        Please check if address is written correctly
      </span>
    </app-section>
    <app-section v-else-if="fetchProjectsResponseStatus === 409">
      <span
        class="private-public-text"
        style="padding-top: 25px; padding-left: 25px"
      >
        <b>You don't have permission to access this project</b><br />
        You already requested access
      </span>
    </app-section>
    <div slot="right" class="panel">
      <upload-panel v-if="upload" :namespace="namespace" class="my-1 mr-1" />
    </div>
  </div>
</template>

<script lang="ts">
import { mapActions, mapState } from 'pinia'
import { TabPanelPassThroughOptions } from 'primevue/tabpanel'
import { defineComponent, PropType } from 'vue'
import { CopyIcon, DownloadIcon, SquareMinusIcon } from 'vue-tabler-icons'

import { AppContainer, AppSection } from '@/common'
import ActionButton from '@/common/components/ActionButton.vue'
import { waitCursor } from '@/common/html_utils'
import { USER_ROLE_NAME_BY_ROLE, UserRole } from '@/common/permission_utils'
import ConfirmDialog from '@/modules/dialog/components/ConfirmDialog.vue'
import { useDialogStore } from '@/modules/dialog/store'
import { useLayoutStore } from '@/modules/layout/store'
import { useNotificationStore } from '@/modules/notification/store'
import ProjectShareButton from '@/modules/project/components/ProjectShareButton.vue'
import UploadPanel from '@/modules/project/components/UploadPanel.vue'
import { ProjectApi } from '@/modules/project/projectApi'
import { useProjectStore } from '@/modules/project/store'
import { useUserStore } from '@/modules/user/store'

interface TabItem {
  route: string
}

export default defineComponent({
  name: 'ProjectViewTemplate',
  components: {
    ActionButton,
    ProjectShareButton,
    UploadPanel,
    CopyIcon,
    DownloadIcon,
    SquareMinusIcon,
    AppContainer,
    AppSection
  },
  props: {
    /**  Show namespace (ws) label in breadcrumb of page */
    showNamespace: {
      type: Boolean as PropType<boolean>,
      default: true
    },
    namespace: String,
    projectName: String,
    location: {
      type: String,
      default: ''
    },
    showSettings: Boolean as PropType<boolean>,
    showHistory: { type: Boolean as PropType<boolean>, default: true },
    hideCloneButton: {
      type: Boolean,
      default: false
    },
    mapRoute: String
  },
  data() {
    return {
      fetchProjectsResponseStatus: null,
      tab: null
    }
  },
  computed: {
    ...mapState(useLayoutStore, ['drawer']),
    ...mapState(useProjectStore, ['project', 'uploads']),
    ...mapState(useUserStore, ['loggedUser']),
    ...mapState(useProjectStore, ['isProjectOwner']),
    ...mapState(useUserStore, ['currentWorkspace', 'isLoggedIn']),

    tabs(): TabItem[] {
      const defaultTabs: TabItem[] = [
        {
          route: 'project-tree'
        }
      ]

      if (this.loggedUser) {
        // If map in slots, add route to map tab
        if (this.$slots['map.tab']) {
          defaultTabs.push({
            route: this.mapRoute
          })
        }
        if (this.showHistory) {
          defaultTabs.push({
            route: 'project-versions'
          })
        }
        if (this.showSettings) {
          defaultTabs.push({
            route: 'project-settings'
          })
        }
      }
      return defaultTabs
    },

    activeTabIndex(): number {
      return this.tabs.findIndex((item) => item.route === this.$route.name)
    },

    /** Rewrite of styles for TabPanels */
    ptHeaderAction(): TabPanelPassThroughOptions {
      return {
        headerAction({ context }) {
          // Custom handling of active styles for tabs
          return {
            style: {
              backgroundColor: 'transparent',
              borderBottomColor: context.active
                ? 'var(--forest-color)'
                : 'transparent'
            },
            class: ['hover:border-400', { 'text-color-forest': context.active }]
          }
        }
      }
    },

    canCloneProject() {
      return this.isLoggedIn && !this.hideCloneButton
    },

    canLeaveProject() {
      return (
        this.project?.workspace_id === this.currentWorkspace?.id &&
        this.currentWorkspace?.role === USER_ROLE_NAME_BY_ROLE[UserRole.guest]
      )
    },

    upload() {
      return this.project && this.uploads[this.project.path]
    },
    downloadUrl() {
      if (this.$route.name === 'project-versions-detail') {
        return ProjectApi.constructDownloadProjectVersionUrl(
          this.namespace,
          this.projectName,
          this.$route.params.version_id as string
        )
      } else {
        return this.constructDownloadProjectUrl({
          namespace: this.namespace,
          projectName: this.projectName
        })
      }
    }
  },
  async created() {
    if (
      !this.project ||
      this.project.name !== this.projectName ||
      this.project.namespace !== this.namespace
    ) {
      this.setProject({ project: null })
      await this.getProject()
    }
  },
  watch: {
    project() {
      if (
        !this.project ||
        this.project.name !== this.projectName ||
        this.project.namespace !== this.namespace
      ) {
        this.setProject({ project: null })
        this.getProject()
      }
    }
  },
  methods: {
    ...mapActions(useProjectStore, [
      'downloadArchive',
      'fetchProjectDetail',
      'unsubscribeProject',
      'constructDownloadProjectUrl'
    ]),
    ...mapActions(useProjectStore, ['setProject']),
    ...mapActions(useDialogStore, { showDialog: 'show' }),
    ...mapActions(useNotificationStore, ['error', 'show']),

    setFetchProjectResponseStatus(status) {
      this.fetchProjectsResponseStatus = status
    },
    async getProject() {
      await new Promise((resolve) => {
        resolve(
          this.fetchProjectDetail({
            callbackStatus: this.setFetchProjectResponseStatus,
            projectName: this.projectName,
            namespace: this.namespace,
            isLoggedUser: !!this.loggedUser
          })
        )
      })
    },
    cloneDialog() {
      this.$emit('open-clone-dialog')
    },
    createAccessRequest() {
      waitCursor(true)
      ProjectApi.createProjectAccessRequest(
        this.namespace,
        this.projectName,
        true
      )
        .then(() => {
          waitCursor(false)
          this.show({
            text: 'Access has been requested'
          })
          this.$router.push({
            name: 'projects'
          })
        })
        .catch(() => {
          this.error({
            text: 'Failed to request'
          })
          waitCursor(false)
        })
    },
    unsubscribeDialog() {
      const projPath = `${this.namespace}/${this.projectName}`
      const props = {
        text: `Are you sure to leave the project <strong>${projPath}</strong>?
        You will not have access to it anymore.`,
        confirmText: 'OK'
      }
      const listeners = {
        confirm: async () => {
          await this.unsubscribeProject({ id: this.project.id })
          if (!this.project) {
            await this.$router.push('/dashboard')
          }
        }
      }
      this.showDialog({
        component: ConfirmDialog,
        params: {
          props,
          listeners,
          dialog: { maxWidth: 500, header: 'Leave project' }
        }
      })
    },

    /**
     * Handles clicking on a tab by index.
     *
     * @param index - The index of the clicked tab.
     */
    tabClick(index: number) {
      this.$router.push({
        name: this.tabs[index].route,
        params: { namespace: this.namespace, projectName: this.project.name }
      })
    }
  }
})
</script>

<style lang="scss" scoped></style>
