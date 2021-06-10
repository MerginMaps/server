# Copyright (C) 2018 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

<template>
  <v-card v-on:keyup.enter="createProject">
    <v-card-title>
      <span class="headline">New project</span>
    </v-card-title>
    <v-card-text>
      <p
        class="text-xs-center red--text"
        v-text="error"
      />
      <v-text-field
        autofocus
        label="name"
        v-model="name"
      />
      <v-select
        label="Template project"
        v-model="template"
        :items="templates"
        item-text="name"
        item-value="name"
        clearable
      />
      <input type="hidden" id="template-input" :value="template"/>
      <v-select
        label="Project owner"
        v-model="namespace"
        :items="namespaces"
        item-text="name"
        item-value="name"
        clearable
      />
      <v-checkbox
        label="Public"
        color="primary"
        v-model="isPublic"
      />
    </v-card-text>
    <v-card-actions>
      <v-spacer/>
      <v-btn @click="$dialog.close" class="black--text">
        Close
      </v-btn>
      <v-btn
        id="create-project-btn"
        class="primary"
        :disabled="!name || !namespace"
        @click="createProject"
      >
        Create
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script>
import { waitCursor } from '../util'
import { postRetryCond } from '../http'

export default {
  name: 'new-project',
  data () {
    return {
      name: '',
      isPublic: false,
      templates: [],
      template: null,
      namespaces: [],
      namespace: null,
      error: null
    }
  },
  created () {
    this.fetchTemplates()
    this.fetchNamespaces()
    this.namespace = this.$store.state.app.user.username
  },
  methods: {
    async fetchTemplates () {
      const resp = await this.$http.get('/app/templates')
      this.templates = resp.data
    },
    async fetchNamespaces () {
      const username = this.$store.state.app.user.username
      this.namespaces.push(username)
      const writableOrgNamespaces = this.$store.state.organisations.filter(
        o => (o.writers.includes(username) || o.admins.includes(username) || o.owners.includes(username)) && o.active
      )
      this.namespaces = this.namespaces.concat(writableOrgNamespaces)
    },
    createProject () {
      const data = {
        name: this.name.trim(),
        public: this.isPublic
      }
      if (this.template) {
        data.template = this.template
      }
      waitCursor(true)
      const params = {
        'axios-retry': {
          retries: 5,
          retryCondition: error => postRetryCond(error)
        }
      }
      this.$http.post(`/v1/project/${this.namespace}`, data, params)
        .then(() => {
          waitCursor(false)
          this.$store.commit('project', null)
          this.$router.push({ name: 'project', params: { namespace: this.namespace, projectName: this.name.trim() } })
          this.$dialog.close()
        })
        .catch(err => {
          this.error = (err.response && err.response.data.detail) || 'Error'
          waitCursor(false)
        })
    }
  }
}
</script>
