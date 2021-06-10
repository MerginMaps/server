# Copyright (C) 2020 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

<template>
  <v-card class="layout column main-content fill-height" flat>
    <v-card-title>
      <h2 class="primary--text"> Projects </h2>
      </v-card-title>
    <warning-message v-if="isAdmin || isOwner"/>

    <v-card-text>
      <v-divider/>
      <div class="py-2"/>
      <projects-table :key="key" :namespace="name" :show-namespace="false" :show-tags="false"></projects-table>
      <div class="py-2"/>
    </v-card-text>

    <v-card text flat class="table" v-if="isAdmin">
      <v-card-title>
        <h3>Projects transfer request</h3>
      </v-card-title>
      <v-card-text>
        <transfers-table :namespace="name" />
      </v-card-text>
    </v-card>

  </v-card>
</template>

<script>
import { mapState } from 'vuex'
import TransfersTable from '@/components/TransfersTable'
import ProjectsTable from '@/components/ProjectsTable'
import MerginAPIMixin from '@/mixins/MerginAPI'
import OrganisationMixin from '@/mixins/Organisation'
import WarningMessage from '@/components/WarningMessage'

export default {
  name: 'organisations-projects',
  mixins: [OrganisationMixin, MerginAPIMixin],
  components: { TransfersTable, ProjectsTable, WarningMessage },
  props: {
    name: String
  },
  data () {
    return {
      projects: [],
      dialog: false,
      key: 0
    }
  },
  computed: {
    ...mapState(['app', 'organisation', 'transfers']),
    isOwner () {
      if (this.organisation && this.app.user) {
        return this.organisation.owners.includes(this.app.user.username)
      }
      return null
    },
    isAdmin () {
      if (this.organisation && this.app.user) {
        return this.isOwner || this.organisation.admins.includes(this.app.user.username)
      }
      return null
    }
  },
  watch: {
    transfers: function () {
      this.key += 1
    }
  }
}
</script>

<style lang="scss" scoped>
.main-content {
  overflow: unset;
}
.profile {
  margin-bottom: 20px;

h2 {
    color: #2D4470;
    margin-bottom: 10px;
  }
}
.table{
  margin-top: 0px;
  padding-right: 10px;
  button {
    padding-left: 10px;
    height: 35px;
    padding-right: 10px;
    width: 100%;
    i {
      font-size: 13px;
    }
  }
}

@media (max-width : 480px) {
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
