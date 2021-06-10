# Copyright (C) 2020 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

<template>
  <page-view>
    <v-layout class="column fill-height ml-10">
      <v-row>
        <v-layout align-center shrink>
          <h3 class="ml-1 my-2">
            <span v-if="namespace"> <v-icon class="arrow">chevron_right</v-icon> {{ namespace }}</span>
          </h3>
          <v-spacer/>
          <portal-target name="additional-action"/>
          <div v-if="this.$route.meta.flag !== 'request'">
          </div>
          <div v-else>
            <portal-target name="accept-request-button"/>
          </div>
        </v-layout>
      </v-row>
      <v-row>
        <v-col>
          <v-card class="table">
            <v-card-title>
              Active Projects
            </v-card-title>
            <v-card-text>
              <projects-table
                :key="namespace"
                :show-namespace="true"
                :namespace="namespace"
                :asAdmin="true"
                show-tags
                />
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
      <v-row>
        <v-col>
          <v-card class="table">
            <v-card-title>
              Removed Projects
            </v-card-title>
            <v-card-text>
              <removed-projects-table/>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </v-layout>
  </page-view>
</template>

<script>
import { mapState } from 'vuex'

import PageView from '@/views/PageView'
import ProjectsTable from '@/admin/views/dashboard/components/ProjectsTable'
import RemovedProjectsTable from '@/admin/views/dashboard/components/RemovedProjectsTable'

export default {
  name: 'admin-projects-list',
  components: { PageView, ProjectsTable, RemovedProjectsTable },
  props: {
    namespace: String
  },
  data () {
    return {
      asAdmin: true
    }
  },
  computed: {
    ...mapState(['app'])
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
</style>
