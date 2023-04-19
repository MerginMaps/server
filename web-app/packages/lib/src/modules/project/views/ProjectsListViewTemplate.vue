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
    <v-layout v-if="!namespace" class="column fill-height main-content">
      <v-layout shrink class="column ml-1 my-2 pl-3">
        <v-layout align-center shrink>
          <h1 class="primary--text">
            {{ header }}
            <span v-if="namespace">
              <v-icon class="arrow">chevron_right</v-icon> {{ namespace }}</span
            >
          </h1>
          <v-spacer />
          <portal-target name="additional-action" />
          <div class="action-button" v-if="canCreateProject">
            <action-button
              v-if="loggedUser && loggedUser.email"
              @click="newProjectDialog"
              data-cy="action-button-create"
            >
              <template #icon>
                <plus-icon />
              </template>
              Create
            </action-button>
          </div>
          <div class="action-button" v-if="!onlyPublic">
            <action-button
              v-if="loggedUser && loggedUser.email"
              @click="findPublicProjects"
            >
              <template #icon>
                <search-icon />
              </template>
              Find public projects
            </action-button>
          </div>
        </v-layout>
        <br />
        <v-divider />
      </v-layout>
      <v-card class="table" style="-webkit-box-shadow: none; box-shadow: none">
        <v-card-text>
          <slot name="projects" :onlyPublic="onlyPublic"></slot>
        </v-card-text>
      </v-card>
    </v-layout>
    <v-layout v-else class="column fill-height main-content">
      <v-card>
        <span
          class="private-public-text"
          style="padding-top: 25px; padding-left: 25px"
        >
          <b>Namespace not found</b><br />
          Please check if address is written correctly
        </span>
      </v-card>
    </v-layout>
  </page-view>
</template>

<script lang="ts">
import Vue from 'vue'
import { PlusIcon, SearchIcon } from 'vue-tabler-icons'
import { mapState } from 'vuex'

import ActionButton from '@/common/components/ActionButton.vue'
import PageView from '@/modules/layout/components/PageView.vue'
import ProjectForm from '@/modules/project/components/ProjectForm.vue'

export default Vue.extend({
  name: 'ProjectsListView',
  components: { ActionButton, PageView, PlusIcon, SearchIcon },
  props: {
    namespace: String,
    canCreateProject: Boolean
  },
  computed: {
    ...mapState('userModule', ['loggedUser']),
    ...mapState('layoutModule', ['drawer']),
    header() {
      return this.onlyPublic ? 'Mergin Maps public projects' : 'Projects'
    },
    onlyPublic() {
      return this.$route.name === 'explore' || !this.loggedUser?.email
    }
  },
  methods: {
    findPublicProjects() {
      this.$router.push({
        name: 'explore'
      })
    },
    newProjectDialog() {
      const dialog = { maxWidth: 500, persistent: true }
      this.$store.dispatch('dialogModule/show', {
        component: ProjectForm,
        params: {
          listeners: {
            error: (err) => this.$emit('new-project-error', err)
          },
          dialog
        }
      })
    }
  }
})
</script>

<style lang="scss" scoped>
h1 a {
  text-decoration: none;
}

.v-card.table {
  min-height: unset;
  overflow: unset;
}

.arrow {
  color: black;
  font-size: large;
}

@media (max-width: 400px) {
  .action-button {
    width: 135px;
  }
}

.action-button {
  div {
    display: inline-block;
  }
}

.toggle-toolbar {
  position: fixed;
  left: 5px;
  z-index: 100;
  bottom: 20px;
}
</style>
