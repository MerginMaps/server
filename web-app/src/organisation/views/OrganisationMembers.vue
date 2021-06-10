# Copyright (C) 2020 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

<template>
  <page-view>
    <v-card class="layout column main-content fill-height" flat v-if="isMember">
      <v-card-text>
          <h1 class="primary--text"> Members </h1>
          <br>
          <v-divider/>
          <div class="py-2"/>
            <organisation-permissions
              :organisation="organisation"
              :appUser="app.user"
              @save-organisation="saveSettings(...arguments)"
            />
          <div class="py-2"/>
        <v-divider/>
      </v-card-text>
    </v-card>
  </page-view>
</template>

<script>
import union from 'lodash/union'
import { mapState } from 'vuex'
import OrganisationMixin from '../../mixins/Organisation'
import PageView from '@/views/PageView'
import OrganisationPermissions from '@/organisation/components/OrganisationPermissions'
import MerginAPIMixin from '@/mixins/MerginAPI'

export default {
  name: 'organisation-members',
  mixins: [OrganisationMixin, MerginAPIMixin],
  components: { PageView, OrganisationPermissions },
  props: { name: String },
  computed: {
    ...mapState(['app', 'organisation']),
    isMember () {
      if (this.organisation && this.app.user) {
        return this.isAdmin || union(this.organisation.writers, this.organisation.readers).includes(this.app.user.username)
      }
      return null
    }
  },
  methods: {
    saveSettings (access) {
      // check access obj is valid
      const empty = (element) => !element.length
      const invalidKey = Object.values(access).some(empty)
      if (invalidKey) {
        this.$notification.error('Failed to save: Invalid update of permissions')
        return
      }
      this.updateMembers(this.name, access)
    }
  }
}
</script>

<style lang="scss" scoped>
.profile{
  margin-bottom: 20px;
  h2 {
    color: #2D4470;
    margin-bottom: 10px;
  }
  button {
    padding-left: 10px;
    height: 35px;
    padding-right: 10px;
    width: 100%;
    i {
      font-size: 13px;
    }
  }
  .align-center{
    padding-top: 10px;
    padding-bottom: 10px;
    align-items: flex-start;
    padding-right: 10px;
  }
  .section{
    margin-right: 10px;
    ul {
      padding-left: 0;
    }
    li {
      list-style: none;
      b {
        width: 150px;
        display: inline-block;
      }
    }
    .v-icon {
      font-size: 18px;
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
