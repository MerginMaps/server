<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <div>
    <template v-if="project">
      <app-container class="flex justify-content-end xl:pb-1 lg:-mb-6">
        <!-- Z indexes based on minus margin, its not possible to add additional buttons to tab view -->
        <div class="relative z-1">
          <!-- Toolbar -->
          <portal-target name="project-toolbar" class="layout row shrink" />
          <slot name="shareButton">
            <project-share-button />
          </slot>
          <PButton
            severity="secondary"
            @click="downloadArchive({ url: downloadUrl })"
            data-cy="project-download-btn"
            icon="ti ti-download"
            class="mr-2"
            label="Download"
          />
          <PButton
            severity="secondary"
            @click="cloneDialog"
            v-if="canCloneProject"
            data-cy="project-clone-btn"
            icon="ti ti-copy"
            label="Clone"
            class="mr-2"
          />
          <PButton
            severity="secondary"
            @click="leaveDialog"
            data-cy="project-leave-btn"
            icon="ti ti-logout"
            label="Leave project"
            v-if="canLeaveProject"
          />
        </div>
      </app-container>

      <PTabView
        :active-index="activeTabIndex"
        @tab-click="(e) => tabClick(e.index)"
        :pt="{
          root: {
            class: 'relative z-auto mb-1'
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
        <PTabPanel :header="tabs[0].header" :pt="ptHeaderAction"></PTabPanel>
        <slot name="map.tab" :ptHeaderAction="ptHeaderAction" />
        <!-- Render other tabs with header -->
        <PTabPanel
          v-for="tab in tabs.slice(1).filter((item) => item.header)"
          :header="tab.header"
          :pt="ptHeaderAction"
          :key="tab.route"
        ></PTabPanel>
      </PTabView>
      <router-view />
    </template>
    <app-container v-else-if="fetchProjectsResponseStatus">
      <app-section v-if="fetchProjectsResponseStatus === 403">
        <div class="flex flex-column align-items-center p-4 text-center">
          <img src="@/assets/map-circle.svg" alt="No project" />
          <p class="font-semibold">This is a private project</p>
          <p class="text-sm opacity-80 mt-2 mb-4">
            You don't have permissions to access this project.
          </p>
          <PButton id="request-access-btn" @click="createAccessRequest"
            >Request access</PButton
          >
        </div>
      </app-section>
      <app-section v-else-if="fetchProjectsResponseStatus === 404">
        <div class="flex flex-column align-items-center p-4 text-center">
          <img src="@/assets/map-circle.svg" alt="No project" />
          <p class="font-semibold">Project not found</p>
          <p class="text-sm opacity-80 mt-2 mb-4">
            Please check if address is written correctly
          </p>
        </div>
      </app-section>
      <app-section v-else-if="fetchProjectsResponseStatus === 409">
        <div class="flex flex-column align-items-center p-4 text-center">
          <img src="@/assets/map-circle.svg" alt="No project" />
          <p class="font-semibold">
            You don't have permission to access this project
          </p>
          <p class="text-sm opacity-80 mt-2 mb-4">
            You already requested access
          </p>
        </div>
      </app-section>
    </app-container>
    <div slot="right">
      <upload-panel v-if="upload" :namespace="namespace" class="my-1 mr-1" />
    </div>
  </div>
</template>

<script lang="ts">
import { mapActions, mapState } from 'pinia'
import { TabPanelPassThroughOptions } from 'primevue/tabpanel'
import { defineComponent, PropType } from 'vue'

import { AppContainer, AppSection } from '@/common'
import { waitCursor } from '@/common/html_utils'
import { USER_ROLE_NAME_BY_ROLE, UserRole } from '@/common/permission_utils'
import { ConfirmDialogProps, ProjectRouteName } from '@/modules'
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
  header?: string
}

export default defineComponent({
  name: 'ProjectViewTemplate',
  components: {
    ProjectShareButton,
    UploadPanel,
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
      tab: null,
      value: 'read'
    }
  },
  computed: {
    ...mapState(useLayoutStore, ['drawer']),
    ...mapState(useProjectStore, ['project', 'uploads']),
    ...mapState(useUserStore, ['loggedUser']),
    ...mapState(useProjectStore, ['isProjectOwner']),
    ...mapState(useUserStore, ['currentWorkspace', 'isLoggedIn']),

    tabs(): TabItem[] {
      const tabs: TabItem[] = [
        {
          route: ProjectRouteName.ProjectTree,
          header: 'Files'
        }
      ]

      if (this.loggedUser) {
        // If map in slots, add route to map tab
        if (this.$slots['map.tab']) {
          tabs.push({
            route: this.mapRoute
          })
        }
        if (this.showHistory) {
          tabs.push({
            route: ProjectRouteName.ProjectHistory,
            header: 'History'
          })
        }
        if (this.showSettings) {
          tabs.push({
            route: ProjectRouteName.ProjectSettings,
            header: 'Settings'
          })
        }
      }
      return tabs
    },

    activeTabIndex(): number {
      return this.tabs.findIndex((item) =>
        this.$route.matched.some((m) => m.name === item.route)
      )
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
    leaveDialog() {
      const projPath = this.showNamespace
        ? `${this.namespace}/${this.projectName}`
        : this.projectName
      const props: ConfirmDialogProps = {
        text: `Are you sure to leave the project ${projPath}?`,
        description: 'You will not have access to it anymore.',
        severity: 'danger',
        confirmText: 'Yes',
        cancelText: 'No'
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
          dialog: { header: 'Leave project' }
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
        name: this.tabs[index].route
      })
    }
  }
})
</script>

<style lang="scss" scoped></style>
