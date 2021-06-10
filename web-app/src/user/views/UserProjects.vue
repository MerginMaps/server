# Copyright (C) 2018 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

<template>
  <v-card class="layout column main-content fill-height" flat>
    <v-card-title>
      <h2 class="primary--text"> Projects </h2>
      </v-card-title>

    <v-card-text>
      <v-divider/>
      <div class="py-2"/>
      <b>
        My projects
        <span v-if="userProjects">
           (<router-link :to="{name: 'my_projects'}">{{ userProjects.count }}</router-link>)
        </span>
        <progress-spinner v-else/>
        <v-spacer/>
        Projects shared with me
        <span v-if="sharedProjects">
           (<router-link :to="{name: 'shared_projects'}">{{ sharedProjects.count }}</router-link>)
        </span>
        <progress-spinner v-else/>
        <v-spacer/>
      </b>
      <portal-target name="additional-action"/>
      <div class="py-2"/>
      <v-divider/>
    </v-card-text>

    <v-card text flat class="table">
      <v-card-title>
        <h3>Projects transfer requests</h3>
      </v-card-title>
      <v-card-text>
        <transfers-table :namespace="name" />
      </v-card-text>
    </v-card>
    <v-card text flat class="table">
      <v-card-title>
        <h3>Projects access requests</h3>
      </v-card-title>
      <v-card-text>
        <project-access-table/>
      </v-card-text>
    </v-card>

  </v-card>
</template>

<script>
import { mapState } from 'vuex'
import ProgressSpinner from '@/components/ProgressSpinner'
import TransfersTable from '@/components/TransfersTable'
import ProjectAccessTable from '@/components/ProjectAccessRequestTable'
import MerginAPIMixin from '@/mixins/MerginAPI'

export default {
  name: 'user-projects',
  mixins: [MerginAPIMixin],
  components: { ProgressSpinner, TransfersTable, ProjectAccessTable },
  props: {
    name: String
  },
  data () {
    return {
      userInfo: null,
      userProjects: null,
      sharedProjects: null,
      dialog: false,
      ignored_profile: ['active', 'disk_usage', 'is_admin', 'storage_limit', 'id']
    }
  },
  computed: {
    ...mapState(['app', 'users', 'transfers'])
  },
  created () {
    this.fetchUserProjects()
    this.fetchSharedProjects()
  },
  watch: {
    name: function () {
      this.fetchUserProjects()
      this.fetchSharedProjects()
    },
    transfers: function () {
      this.fetchUserProjects()
      this.fetchSharedProjects()
    }
  },
  methods: {
    fetchUserProjects () {
      const params = { user: this.name, flag: 'created', page: 1, per_page: 1 }
      this.$http.get('/v1/project/paginated', { params })
        .then(resp => {
          this.userProjects = resp.data
        })
        .catch(() => this.$notification.error("Failed to fetch user's project"))
    },
    fetchSharedProjects () {
      const params = { user: this.name, flag: 'shared', page: 1, per_page: 1 }
      this.$http.get('/v1/project/paginated', { params })
        .then(resp => {
          this.sharedProjects = resp.data
        })
        .catch(() => this.$notification.error('Failed to fetch shared projects with user'))
    }
  }
}
</script>

<style lang="scss" scoped>
.main-content {
  overflow: auto;
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
