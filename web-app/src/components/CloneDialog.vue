# Copyright (C) 2019 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

<template>
  <v-card v-on:keyup.enter="createProject">
    <v-card-title>
      <span class="headline">Clone Project</span>
    </v-card-title>
    <v-card-text>
      <p
        class="text-xs-center red--text"
        v-text="error"
      />
      <v-text-field
        autofocus
        label="new project"
        v-model="name"
      />
       <v-select
        label="Project owner"
        v-model="newNamespace"
        :items="namespaces"
        item-text="name"
        item-value="name"
        clearable
      />
    </v-card-text>
    <v-card-actions>
      <v-spacer/>
      <v-btn @click="$dialog.close">
        Close
      </v-btn>
      <v-btn
        id="clone-project-btn"
        class="primary"
        :disabled="!name || !newNamespace"
        @click="cloneProject"
      >
        Clone
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script>
import { waitCursor } from '../util'
import { postRetryCond } from '../http'

export default {
  name: 'clone-project',
  props: {
    namespace: String,
    project: String
  },
  data () {
    return {
      name: '',
      error: null,
      namespaces: [],
      newNamespace: null
    }
  },
  created () {
    this.fetchNamespaces()
    this.newNamespace = this.app.user.username
    this.name = this.project
  },
  computed: {
    app () {
      return this.$store.state.app
    }
  },
  methods: {
    cloneProject () {
      const data = {
        project: this.name.trim(),
        namespace: this.newNamespace
      }
      waitCursor(true)
      const params = {
        'axios-retry': {
          retries: 5,
          retryCondition: error => postRetryCond(error)
        }
      }
      this.$http.post(`/v1/project/clone/${this.namespace}/${this.project}`, data, params)
        .then(() => {
          waitCursor(false)
          this.$dialog.close()
          this.$store.commit('project', null)
          this.$router.push({ name: 'project', params: { namespace: this.newNamespace, projectName: this.name.trim() } })
        })
        .catch(err => {
          this.error = (err.response && err.response.data.detail) || 'Error'
          waitCursor(false)
        })
    },
    async fetchNamespaces () {
      const username = this.$store.state.app.user.username
      this.namespaces.push(username)
      this.namespaces = this.namespaces.concat(this.$store.state.organisations.filter(function (item) {
        return item.writers.includes(username)
      }))
    }
  }
}
</script>
