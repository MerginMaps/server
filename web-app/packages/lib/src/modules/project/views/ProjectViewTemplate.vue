<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <page-view
    :style="`padding-left: ${
      drawer ? 260 : 20
    }px; overflow-y: auto; padding-right:20px; margin-right: 0px;`"
  >
    <div slot="left" class="panel" />
    <v-layout class="column fill-height project-page main-content">
      <v-card v-if="project" style="margin-bottom: 0" outlined>
        <!-- Toolbar -->
        <v-layout class="row align-center toolbar">
          <div class="breadcrumbs" style="font-size: 20px">
            <v-icon color="primary">map</v-icon>
            <!--            TODO: router link is removed for now, replaced with plain text -->
            <!--            <router-link-->
            <!--              v-if="isNamespaceVisible"-->
            <!--              :to="{-->
            <!--                name: 'namespace-projects',-->
            <!--                namespace: project.namespace-->
            <!--              }"-->
            <!--              v-text="project.namespace"-->
            <!--            />-->
            <span v-if="isNamespaceVisible" class="primary--text">{{
              project.namespace
            }}</span>
            <span v-if="isNamespaceVisible" class="primary--text">/</span>
            <router-link
              :to="{
                name: 'project',
                project: project
              }"
            >
              <b>{{ project.name }}</b></router-link
            >

            <router-link
              :to="{
                name: 'project-versions-detail'
              }"
              v-slot="{ href, route, navigate }"
            >
              <span v-if="route.params.version_id">
                &gt;
                <a :href="href" @click="navigate">
                  {{ route.params.version_id }}
                </a>
              </span>
            </router-link>
            <router-link
              :to="{ name: 'file-version-detail' }"
              v-slot="{ href, route, navigate }"
            >
              <span v-if="route.params.path">
                &gt;
                <a :href="href" @click="navigate">
                  {{ route.params.path }}
                </a>
              </span>
            </router-link>
          </div>
          <v-spacer />
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
        </v-layout>

        <v-card class="layout column fill-height" flat>
          <v-card-title>
            <v-tabs left-active v-model="tab" show-arrows>
              <v-tabs-slider color="primary"></v-tabs-slider>
              <v-tab
                key="files"
                :to="{
                  name: `project-tree`,
                  params: { namespace: namespace, projectName: project.name }
                }"
                >Files
              </v-tab>
              <slot name="map.tab" v-if="loggedUser" />
              <v-tab
                key="history"
                :to="{
                  name: `project-versions`,
                  params: { namespace: namespace, projectName: project.name }
                }"
                >History
              </v-tab>
              <v-tab
                key="settings"
                :to="{
                  name: `project-settings`,
                  params: { namespace: namespace, projectName: project.name }
                }"
                v-if="loggedUser && showSettings"
                >Settings
              </v-tab>
            </v-tabs>
          </v-card-title>
          <v-divider></v-divider>
          <router-view v-if="project" class="content-container" />
        </v-card>
      </v-card>
      <v-card v-else-if="fetchProjectsResponseStatus === 403">
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
      </v-card>
      <v-card v-else-if="fetchProjectsResponseStatus === 404">
        <span
          class="private-public-text"
          style="padding-top: 25px; padding-left: 25px"
        >
          <b>Project not found</b><br />
          Please check if address is written correctly
        </span>
      </v-card>
      <v-card v-else-if="fetchProjectsResponseStatus === 409">
        <span
          class="private-public-text"
          style="padding-top: 25px; padding-left: 25px"
        >
          <b>You don't have permission to access this project</b><br />
          You already requested access
        </span>
      </v-card>
      <drop-area
        v-if="
          project &&
          $route.name === 'project-tree' &&
          project.permissions &&
          project.permissions.upload
        "
        class="drop-area"
        :location="location"
        data-cy="project-drop-area"
      >
        <v-layout row wrap align-center class="drag-drop-text">
          <span>
            <v-icon>publish</v-icon> Drag & drop here or click and select
            file(s) to upload
          </span>
        </v-layout>
      </drop-area>
    </v-layout>
    <div slot="right" class="panel">
      <upload-panel v-if="upload" :namespace="namespace" class="my-1 mr-1" />
    </div>
  </page-view>
</template>

<script lang="ts">
import { mapActions, mapGetters, mapState } from 'pinia'
import { defineComponent } from 'vue'
import { CopyIcon, DownloadIcon, SquareMinusIcon } from 'vue-tabler-icons'

import ActionButton from '@/common/components/ActionButton.vue'
import { waitCursor } from '@/common/html_utils'
import { USER_ROLE_NAME_BY_ROLE, UserRole } from '@/common/permission_utils'
import ConfirmDialog from '@/modules/dialog/components/ConfirmDialog.vue'
import { useDialogStore } from '@/modules/dialog/store'
import PageView from '@/modules/layout/components/PageView.vue'
import { useLayoutStore } from '@/modules/layout/store'
import { useNotificationStore } from '@/modules/notification/store'
import DropArea from '@/modules/project/components/DropArea.vue'
import ProjectShareButton from '@/modules/project/components/ProjectShareButton.vue'
import UploadPanel from '@/modules/project/components/UploadPanel.vue'
import { ProjectApi } from '@/modules/project/projectApi'
import { useProjectStore } from '@/modules/project/store'
import { useUserStore } from '@/modules/user/store'

export default defineComponent({
  name: 'ProjectViewTemplate',
  components: {
    ActionButton,
    ProjectShareButton,
    PageView,
    UploadPanel,
    DropArea,
    CopyIcon,
    DownloadIcon,
    SquareMinusIcon
  },
  props: {
    // forces to show namespace (also on non-public projects)
    showNamespace: {
      type: Boolean,
      default: false
    },
    // forces to hide namespace (also on public projects)
    // if both hideNamespace and showNamespace is true, namespace is not shown
    hideNamespace: {
      type: Boolean,
      default: false
    },
    namespace: String,
    projectName: String,
    location: {
      type: String,
      default: ''
    },
    showSettings: Boolean,
    hideCloneButton: {
      type: Boolean,
      default: false
    }
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
    ...mapGetters(useProjectStore, ['isProjectOwner']),
    ...mapGetters(useUserStore, ['currentWorkspace', 'isLoggedIn']),

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
          this.$route.params.version_id
        )
      } else {
        return ProjectApi.constructDownloadProjectUrl(
          this.namespace,
          this.projectName
        )
      }
    },
    isPublic() {
      return this.project?.access?.public
    },
    isNamespaceVisible() {
      return !this.hideNamespace && (this.showNamespace || this.isPublic)
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
      'unsubscribeProject'
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
        params: { props, listeners, dialog: { maxWidth: 500 } }
      })
    }
  }
})
</script>

<style lang="scss" scoped>
.project-page {
  .drop-area {
    max-height: 100%;
    display: flex;
    flex-grow: 1;
    flex-direction: column;
  }

  .v-card {
    display: flex;
    flex-direction: column;
    margin: 0.25em;
    overflow: unset;
    flex-grow: 0;

    .content-container {
      padding: 0.25em 0;
      background-color: #fff;
      flex: 1;
    }
  }

  small {
    opacity: 0.6;
    margin-bottom: 2px;
  }
}

.theme--light.v-card.v-sheet--outlined {
  border: none;
}

.panel {
  flex: 1 1;
  box-sizing: border-box;
  position: relative;
}

.v-card__subtitle,
.v-card__text,
.v-card__title {
  padding: 16px 0 16px 0;
}

.toolbar {
  max-width: 100%;
  margin-right: 0;
  margin-left: 0;
  flex-shrink: 0;
  flex-grow: 0;
  padding: 0.5em 1em;
  background-color: #fafafa;
  border: solid #eee;
  border-width: 1px 0;

  ::v-deep(*) {
    .v-text-field {
      padding-top: 0;
      margin-top: 0;
      font-size: 15px;
    }

    .v-btn {
      padding: 0 0.5em;
      margin: 0.25em;
      min-width: 2em;
    }
  }
}

.breadcrumbs {
  color: #777;

  a {
    text-decoration: none;
    margin: 0 0.25em;
  }
}

.drop-area {
  margin-top: 5px;
  padding-left: 5px;

  .drag-drop-text {
    border: 1px dashed rgba(0, 0, 0, 0.6);
    opacity: 0.6;
    margin: 0.25em 0.25em 0.25em 0.25em;

    span {
      width: 100%;
      text-align: center;
      margin: 20px;
    }

    i {
      transform: rotate(180deg);
    }
  }
}
</style>
