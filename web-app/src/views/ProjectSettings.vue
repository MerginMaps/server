# Copyright (C) 2018 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

<template>
  <v-layout class="settings column">
    <admin-project-permissions v-if="asAdmin"
        v-model="settings.access"
    />
    <project-permissions v-else
      v-model="settings.access"
      :key="key"
      @save-project="saveSettings()"
    />
    <project-access-requests
    />
    <small
      v-for="(error, index) in errors"
      :key="index"
      class="my-1 red--text"
    >
      {{ error }}
    </small>
    <v-layout class="public-private-zone">
      <v-container>
        <!--      <v-divider/>-->
        <v-row>
          <v-col>
      <span class="private-public-text" v-if="settings.access.public">
          <b>This is public project</b><br>
          <span class="description-text">Hide this project from everyone.</span>
      </span>
            <span class="private-public-text" v-else>
          <b>This is private project</b><br>
              <span class="description-text">Make this project visible to anyone.</span>
      </span>
          </v-col>
          <v-col>
            <v-btn
                @click="confirmPublicPrivate()"
                :disabled="!project.access.owners.includes(app.user.id)"
                class="private-public-btn"
                outlined>
              <span v-if="settings.access.public">Make private</span>
              <span v-else>Make public</span>
            </v-btn>
          </v-col>
        </v-row>
        <v-row
            v-if="(project.permissions.update || project.permissions.delete) && !upload && !transfer && isProjectCreator">
          <v-col>
            <span class="private-public-text">
              <b>Transfer project</b><br>
            <span class="description-text">Transfer this project to another user or organisation</span></span>
          </v-col>
          <v-col>
            <v-btn
                @click="transferDialog"
                class="private-public-btn"
                outlined
            >
              <span>Transfer</span>
            </v-btn>
          </v-col>
        </v-row>
        <v-row v-if="project.permissions.delete"
        >
          <v-col>
            <span class="private-public-text">
              <b>Delete project</b><br>
            <span class="description-text">All data will be lost</span></span>
          </v-col>
          <v-col self-align="end">
            <v-btn
                @click="confirmDelete"
                class="private-public-btn"
                outlined
            >
              <span>Delete</span>
            </v-btn>
          </v-col>
        </v-row>
      </v-container>
    </v-layout>
  </v-layout>
</template>

<script>
import { mapState } from 'vuex'
import ProjectPermissions from '@/components/ProjectPermissions'
import ProjectAccessRequests from '@/components/ProjectAccessRequest'
import AdminProjectPermissions from '../admin/views/dashboard/components/AdminProjectPermissions'
import ProjectTransferForm from '@/components/ProjectTransferForm'
import { waitCursor } from '@/util'
import MerginAPIMixin from '@/mixins/MerginAPI'
import OrganisationsMixin from '@/mixins/Organisation'

export default {
  name: 'project-settings',
  mixins: [MerginAPIMixin, OrganisationsMixin],
  components: { AdminProjectPermissions, ProjectPermissions, ProjectAccessRequests },
  props: {
    namespace: String,
    projectName: String,
    asAdmin: {
      type: Boolean,
      default: false
    }
  },
  data () {
    return {
      settings: {},
      key: 0
    }
  },
  computed: {
    ...mapState(['app', 'project', 'uploads', 'transfers']),
    errors () {
      const errors = []
      if (this.settings.access.ownersnames.length < 1) {
        errors.push("Project doesn't have owner")
      }
      return errors
    },
    isProjectCreator () {
      if (this.project) {
        return this.app.username === this.namespace ? true : this.project.creator === this.app.user.id
      }
      return null
    },
    upload () {
      return this.project && this.uploads[this.project.path]
    },
    transfer () {
      return this.project && this.transfers.find(i => i.project.name === this.projectName) !== undefined
    }
  },
  watch: {
    project: {
      immediate: true,
      handler (project) {
        if (JSON.stringify(this.settings.access) !== JSON.stringify(this.project.access)) {
          this.settings = {
            access: JSON.parse(JSON.stringify(project.access))
          }
        }
        this.key++
      }
    }
  },
  created () {
    if (!this.$store.getters.isProjectOwner && !this.asAdmin) {
      this.$router.push('/projects')
    }
    this.settings = {
      access: JSON.parse(JSON.stringify(this.project.access))
    }
  },
  methods: {
    saveSettings () {
      waitCursor(true)
      this.$http.put(`/v1/project/${this.namespace}/${this.projectName}`, this.settings, { 'axios-retry': { retries: 5 } })
        .then(resp => {
          this.$store.commit('project', resp.data)
          waitCursor(false)
        })
        .catch((err) => {
          this.$notification.error(err.response.data.detail || 'Failed to save project settings')
          waitCursor(false)
        })
    },
    togglePublicPrivate () {
      this.settings.access.public = !this.settings.access.public
    },
    confirmDelete () {
      const props = {
        text: `Are you sure to delete project: ${this.projectName}? All files will be lost. <br> <br> Type in project name to confirm:`,
        confirmText: 'Delete',
        confirmField: {
          label: 'Project name',
          expected: this.projectName
        }
      }
      const listeners = {
        confirm: () => this.deleteProject()
      }
      this.$dialog.prompt({ props, listeners, dialog: { maxWidth: 500 } })
    },
    transferDialog () {
      const dialog = { maxWidth: 500, persistent: true }
      const props = {
        project: this.projectName,
        from_namespace: this.namespace
      }
      const listeners = {
        submit: () => {
          this.fetchTransfers(this.namespace)
        }
      }
      this.$dialog.show(ProjectTransferForm, { props, listeners, dialog })
    },
    confirmPublicPrivate () {
      const props = {
        text: `Do you really want to make this project ${this.settings.access.public ? 'private' : 'public'}?`,
        confirmText: 'Yes'
      }
      const listeners = {
        confirm: () => this.togglePublicPrivate()
      }
      this.$dialog.prompt({ props, listeners, dialog: { maxWidth: 500 } })
    },
    deleteProject () {
      waitCursor(true)
      this.$http.delete(`/v1/project/${this.namespace}/${this.projectName}`, { 'axios-retry': { retries: 5 } })
        .then(() => {
          this.$store.commit('project', null)
          if (this.namespace in this.app.user.profile.organisations) {
            this.getOrganisation(this.namespace)
          } else {
            this.fetchUserProfile(this.app.user.username)
          }
          waitCursor(false)
          this.$router.replace({ name: 'my_projects' })
        })
        .catch(err => {
          this.$notification.error(err.response.data.detail || 'Failed to remove project')
          waitCursor(false)
        })
    }
  }
}
</script>

<style lang="scss" scoped>
.settings {
  display: flex;
  flex-direction: column;
  flex: 1 0 auto;
}
.actions {
  flex: 0 0 auto;
}
.private-public-btn {
  font-size: 12px;
  padding-left: 20px;
  padding-right: 20px;
  background-color: #f3f5f7;
  color: #2d4470;
  text-transform: none;
  min-width: 116px !important;
  float: right;
  border-color: #e0e0e0;
  span {
      font-weight: 700;
  }
}
.private-public-text {
  font-size: 14px;
  color: black;
}
.description-text {
  color: #757575;
}
</style>
