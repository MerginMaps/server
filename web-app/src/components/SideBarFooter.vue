# Copyright (C) 2021 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

<template>
  <div>
    <v-list>
      <div style="color: #2d4470;">
        <span style="color: #8c8c8c"><v-icon style="color: #8c8c8c; margin: 0px 5px 5px 10px;">storage</v-icon>Storage</span>
        <v-spacer/>
        <template
            v-if="this.diskUsage !== undefined && this.storage !== undefined"
        >
          <span style="margin-left: 10px;">{{ this.diskUsage | filesize(null, 0, 'MB') }} of {{ this.storage | filesize(null, 0) }} </span>
          <br/>
          <v-progress-linear
              id="progress"
              :size="55"
              height="15"
              :width="8"
              :value="usage * 100"
              color="primary"
              class="mx-3"
              style="max-width: 80%;"
          >
            {{ Math.ceil(usage * 100) }}%
          </v-progress-linear>
        </template>
      </div>
    </v-list>
  </div>
</template>

<script>
import { mapState } from 'vuex'

export default {
  name: 'SideBarFooter',
  props: {
    sidebarType: String
  },
  computed: {
    ...mapState(['app', 'organisation']),
    usage () {
      if (this.sidebarType === 'user') {
        return this.userProfile.disk_usage / this.userProfile.storage
      } else {
        if (this.organisation) {
          return (this.organisation.storage) ? this.organisation.disk_usage / this.organisation.storage : 0
        }
        return null
      }
    },
    diskUsage () {
      if (this.sidebarType === 'user') {
        return this.userProfile.disk_usage
      } else {
        if (this.organisation) {
          return (this.organisation.disk_usage) ? this.organisation.disk_usage : 0
        }
        return null
      }
    },
    storage () {
      if (this.sidebarType === 'user') {
        return this.userProfile.storage
      } else {
        if (this.organisation) {
          return this.organisation.storage
        }
        return null
      }
    },
    userProfile () {
      return this.app.user.profile
    }
  }
}
</script>

<style lang="sass" scoped>
@import '~vuetify/src/styles/tools/_rtl.sass'

a
  text-decoration: none

.theme--dark.v-navigation-drawer .v-divider
    border-color: hsl(240, 2%, 55%)
</style>
