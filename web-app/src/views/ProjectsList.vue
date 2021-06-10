# Copyright (C) 2018 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

<template>
  <page-view :style="`padding-left: ${drawer ? 260 : 20}px; overflow-y: auto; padding-right:20px; margin-right: 0px;`">
    <v-layout class="column fill-height main-content">
      <v-layout align-center shrink>
        <h3 class="ml-1 my-2 pl-3">
          {{ header }}
          <span v-if="namespace"> <v-icon class="arrow">chevron_right</v-icon> {{ namespace }}</span>
        </h3>
        <v-spacer/>
        <portal-target name="additional-action"/>
        <div v-if="this.$route.meta.flag !== 'request'">
          <div class="action-button">
            <div>
              <v-btn
                v-if="app.user && app.user.email"
                @click="newProjectDialog"
                class="primary--text"
                rounded
              >
                <v-icon class="mr-2">add_circle</v-icon>
                Create
              </v-btn>
            </div>
          </div>
        </div>
        <div v-else>
          <portal-target name="accept-request-button"/>
        </div>

      </v-layout>
      <v-card class="table"
      style="-webkit-box-shadow: none; box-shadow: none;">
        <v-card-text >
          <projects-table
            :key="namespace + $route.name"
            :show-namespace="showNamespace"
            :namespace="namespace"
            :onlyPublic="onlyPublic"
            />
        </v-card-text>
      </v-card>
    </v-layout>
  </page-view>
</template>

<script>
import { mapMutations, mapState } from 'vuex'

import PageView from '@/views/PageView'
import ProjectForm from '@/components/ProjectForm'
import ProjectsTable from '@/components/ProjectsTable'

export default {
  name: 'projects-list',
  components: { PageView, ProjectsTable },
  props: {
    namespace: String
  },
  computed: {
    ...mapState(['app', 'drawer']),
    header () {
      return (this.$route.meta.header !== undefined) ? this.$route.meta.header : 'Projects'
    },
    showNamespace () {
      return this.$route.name !== 'my_projects' && this.namespace === undefined
    },
    onlyPublic () {
      return this.$route.name === 'explore' || !this.app.user
    }
  },
  methods: {
    newProjectDialog () {
      const dialog = { maxWidth: 500, persistent: true }
      this.$dialog.show(ProjectForm, { dialog })
    },
    ...mapMutations({
      setDrawer: 'SET_DRAWER'
    })
  }
}
</script>

<style lang="scss" scoped>
h3 a {
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

@media (max-width : 400px) {
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
