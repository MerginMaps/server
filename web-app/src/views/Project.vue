# Copyright (C) 2018 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

<template>
  <page-view :style="`padding-left: ${drawer ? 260 : 20}px; overflow-y: auto; padding-right:20px; margin-right: 0px;`">
    <div slot="left" class="panel"/>
    <v-layout class="column fill-height project-page main-content">
      <v-card
        v-if="this.project"
        style="margin-bottom: 0"
      outlined>
        <!-- Toolbar -->
        <v-layout class="row align-center toolbar">
          <div class="breadcrumbs" style="font-size: 20px;">
            <v-icon color="primary">map</v-icon>
            <router-link
              :to="{name: `${asAdmin ? 'admin-' : ''}namespace-projects`, namespace: project.namespace}"
              v-text="project.namespace"
            />
            <span>/</span>
            <router-link
              :to="{name: `${asAdmin ? 'admin-' : ''}project`, project: project}"
            > <b>{{project.name}}</b></router-link>

            <router-link
              :to="{name: `${asAdmin ? 'admin-' : ''}project-versions-detail`}"
              v-slot="{ href, route, navigate}">
              <span
                v-if="route.params.version_id">
                &gt;
                <a
                  :href="href"
                  @click="navigate"
                >
                  {{ route.params.version_id }}
                </a>
              </span>
            </router-link>
            <router-link
              :to="{name: `${asAdmin ? 'admin-' : ''}file-version-detail`}"
              v-slot="{ href, route, navigate}">
              <span
                v-if="route.params.path">
                &gt;
                <a
                  :href="href"
                  @click="navigate"
                >
                  {{ route.params.path }}
                </a>
              </span>
            </router-link>
          </div>
          <v-spacer/>
          <portal-target name="project-toolbar" class="layout row shrink"/>
            <v-btn
              :href="downloadUrl"
            >
              <v-icon>archive</v-icon>
              Download
            </v-btn>
            <v-btn
              @click="cloneDialog"
            >
              <v-icon class="pr-1">fa-clone</v-icon>
              Clone
            </v-btn>
        </v-layout>

        <v-card class="layout column  fill-height" flat>
          <v-card-title>
            <v-tabs left-active v-model="tab" show-arrows>
              <v-tabs-slider color="primary"></v-tabs-slider>
              <v-tab key="files" :to="{ name: `${asAdmin ? 'admin-' : ''}project-tree`, params: { namespace: namespace, projectName: project.name }}">Files</v-tab>
              <v-tab key="history" :to="{ name: `${asAdmin ? 'admin-' : ''}project-versions`, params: { namespace: namespace, projectName: project.name }}">History</v-tab>
              <v-tab key="settings" :to="{ name: `${asAdmin ? 'admin-' : ''}project-settings`, params: { namespace: namespace, projectName: project.name }}" v-if="this.app.user && this.$store.getters.isProjectOwner">Settings</v-tab>
            </v-tabs>
          </v-card-title>
          <v-divider></v-divider>
            <router-view v-if="project" class="content-container"/>
        </v-card>
      </v-card>
      <v-card v-else-if="fetchProjectsResponseStatus === 403">
        <v-layout class="public-private-zone" style="padding-top: 25px; padding-left: 25px ;">
      <v-btn id="request-access-btn"
              @click="createAccessRequest">Request access</v-btn>
      <span class="private-public-text">
          <b>This is a private project</b><br>
          You don't have permissions to access this project.
      </span>
    </v-layout>
      </v-card>
      <v-card v-else-if="fetchProjectsResponseStatus === 404">
       <span class="private-public-text" style="padding-top: 25px; padding-left: 25px  ">
          <b>Project not found</b><br>
          Please check if address is written correctly
      </span>
      </v-card>
      <v-card v-else-if="fetchProjectsResponseStatus === 409">
       <span class="private-public-text" style="padding-top: 25px; padding-left: 25px  ">
          <b>You don't have permission to access this project</b><br>
          You already requested access
      </span>
      </v-card>
      <drop-area
        v-if="project && $route.name === 'project-tree' && project.permissions.upload"
        class="drop-area"
        :location="location"
      >
         <v-layout
           row wrap align-center
           class="drag-drop-text">
           <span>
             <v-icon>publish</v-icon> Drag & drop here or click and select file(s) to upload
           </span>
        </v-layout>
      </drop-area>
    </v-layout>
    <div slot="right" class="panel">
      <upload-panel v-if="upload" :namespace="namespace" class="my-1 mr-1"/>
    </div>
  </page-view>
</template>

<script>
import { mapState, mapMutations } from 'vuex'

import PageView from '@/views/PageView'
import UploadPanel from '@/components/UploadPanel'
import DropArea from '@/components/DropArea'
import CloneDialog from '@/components/CloneDialog'
import MerginAPIMixin from '@/mixins/MerginAPI'
import { waitCursor } from '../util'
import { postRetryCond } from '../http'

export default {
  name: 'project',
  mixins: [MerginAPIMixin],
  components: { PageView, UploadPanel, DropArea },
  props: {
    namespace: String,
    projectName: String,
    asAdmin: {
      type: Boolean,
      default: false
    },
    location: {
      type: String,
      default: ''
    }
  },
  data () {
    return {
      fetchProjectsResponseStatus: null,
      tab: null
    }
  },
  computed: {
    ...mapState(['app', 'project', 'uploads', 'transfers', 'drawer']),
    upload () {
      return this.project && this.uploads[this.project.path]
    },
    transfer () {
      return this.project && this.transfers.find(i => i.project.name === this.projectName) !== undefined
    },
    breadcrumbs () {
      if (this.location) {
        const folders = this.location.replace(/\/$/, '').split('/')

        return folders.map((folder, index) => ({
          name: folder,
          link: `/projects/${this.namespace}/${this.projectName}/tree/${folders.slice(0, index + 1).join('/')}`
        }))
      }
      return null
    },
    downloadUrl () {
      if (this.$route.name !== 'project-versions-detail') {
        return this.$http.absUrl(`/v1/project/download/${this.namespace}/${this.projectName}?format=zip`)
      } else {
        return this.$http.absUrl(`/v1/project/download/${this.namespace}/${this.projectName}?version=${this.$route.params.version_id}&format=zip`)
      }
    },
    isProjectCreator () {
      if (this.project) {
        return this.app.username === this.namespace ? true : this.project.creator === this.app.user.id
      }
      return null
    }
  },
  created () {
    if (!this.project || this.project.name !== this.projectName) {
      this.$store.commit('project', null)
      this.getProject()
      if (this.isProjectCreator) { this.fetchTransfers(this.namespace) }
    }
  },
  watch: {
    project () {
      if (!this.project || this.project.name !== this.projectName) {
        this.$store.commit('project', null)
        this.getProject()
        if (this.isProjectCreator) { this.fetchTransfers(this.namespace) }
      }
    }
  },
  methods: {
    async getProject () {
      await new Promise((resolve) => { resolve(this.fetchProject(this.process_error)) })
    },
    ...mapMutations({
      setDrawer: 'SET_DRAWER'
    }),
    process_error (status) {
      this.fetchProjectsResponseStatus = status
      if (status !== 404 && status !== 403) {
        this.$notification.error('Failed to load project data')
      } else if (status === 403 && !this.app.user) {
        this.$router.push(`/login?redirect=/projects/${this.namespace}/${this.projectName}`)
      } else if (status === 403) {
        this.$http('/app/project/access_requests')
          .then(resp => {
            for (const ar of resp.data) {
              if (ar.namespace === this.namespace && ar.project_name === this.projectName) {
                this.fetchProjectsResponseStatus = 409
              }
            }
          })
          .catch(resp => {
            this.$notification.error('Failed to load project access requests data')
          })
      }
    },
    cloneDialog () {
      const props = { namespace: this.namespace, project: this.projectName }
      const dialog = { maxWidth: 500, persistent: true }
      this.$dialog.show(CloneDialog, { props, dialog })
    },
    toSetting () {
      this.$router.replace({ name: `${this.asAdmin ? 'admin-' : ''}project-settings` })
    },
    createAccessRequest () {
      waitCursor(true)
      const params = {
        'axios-retry': {
          retries: 5,
          retryCondition: error => postRetryCond(error)
        }
      }
      this.$http.post(`/app/project/access_request/${this.namespace}/${this.projectName}`, { }, params)
        .then(() => {
          waitCursor(false)
          this.$notification.show('Access has been requested')
          this.$router.push({ name: 'user_projects', params: { username: this.app.user.username } })
        })
        .catch(() => {
          this.$notification.error('Failed to request')
          waitCursor(false)
        })
    }
  }
}
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
      padding: 0.25em 0em;
      background-color: #fff;
      flex: 1;
    }
  }
  small {
    opacity: 0.6;
    margin-bottom: 2px;
  }
}
.theme--light.v-card.v-card--outlined {
    border: none;
}
.panel {
  flex: 1 1;
  box-sizing: border-box;
  position: relative;
}
.v-card__subtitle, .v-card__text, .v-card__title {
    padding: 16px 0px 16px 0px
}
.toolbar {
  max-width: 100%;
  margin-right: 0px;
  margin-left: 0px;
  flex-shrink: 0;
  flex-grow: 0;
  padding: 0.5em 1em;
  background-color: #fafafa;
  border: solid #eee;
  border-width: 1px 0;
  ::v-deep {
    .v-text-field {
      padding-top: 0;
      margin-top: 0;
      font-size: 15px;
    }
    .v-btn {
      padding: 0 0.5em;
      margin: 0.25em;
      min-width: 2em;

      .v-icon {
    color: black;
  }
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

.drop-area{
  margin-top: 5px;
  padding-left: 5px;
  .drag-drop-text{
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
