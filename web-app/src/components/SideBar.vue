# Copyright (C) 2021 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

<template>
  <v-navigation-drawer
    class="user-side-bar d-flex align-start flex-column mb-6"
    id="core-navigation-drawer-user"
    v-model="drawer"
    :expand-on-hover="expandOnHover"
    :right="$vuetify.rtl"
    mobile-break-point="960"
    :dark="barColor !== 'rgba(228, 226, 226, 1), rgba(255, 255, 255, 0.7)'"
    app
    width="260"
    v-bind="$attrs"
    v-if="app.user"
  >

    <div style="height:100%;">
    <v-card
      class="d-flex flex-column"
      flat
      tile
      style="height:100%; width: 260px"
      :outlined="true"
    >
      <v-card
        class="pa-2"
        tile
        :outlined="true"
        style="margin-top: 40px;"
      >

        <v-menu
        v-if="app.user && app.user.email"
        :min-width="150"
        bottom
        left
        offset-y
        origin="top right"
        transition="scale-transition"
      >
        <template v-slot:activator="{ on }">
        <v-btn id="login_btn" v-on="on" text dark :ripple="false" class="icon-btn" style="padding-top: 20px; text-transform: none;">
          <v-icon class="mr-2 primary--text">account_circle</v-icon> <h2 class="primary--text" style="text-align: center">{{profile.username}}</h2><v-icon class="primary--text" >arrow_drop_down</v-icon>
        </v-btn>
                  </template>

        <v-list dense>
          <v-list-item :to="{name: 'dashboard'}">
            <strong> {{ app.user.username }} </strong>
          </v-list-item>
          <v-divider></v-divider>

          <v-list-item v-for="(item, i) in computedOrganisationItems" :key="i" :to="{ name: 'org_projects', params: { name: item.title }}" >
            {{item.title}}
          </v-list-item>
        </v-list>
      </v-menu>

        <v-list nav flat>
          <base-item
              id="item-home"
              key="item-home"
              :item="{title: 'Home',
                      to: '/dashboard'}"
              color="primary"
          />
      </v-list>

      <v-divider style="width: 90%; margin: 5px 0px 5px 0px"/>
        <span style="color: #8c8c8c; font-size: larger">
          <v-icon color="#8c8c8c">folder</v-icon>
          Projects
        </span>
        <v-btn x-small
               color="#ff9800"
               rounded
               style="float: right;"
               @click="newProjectDialog">+ create</v-btn>
      <v-list :expand="true" nav>

        <template v-for="(item, i) in computedItems">
          <base-item
              :id="`item-${i}`"
              :key="`item-${i}`"
              :item="item"
              color="primary"
              class="ma-0"
          />
        </template>
      </v-list>
        <v-divider style="width: 90%; margin: 5px 0px 5px 0px"/>
        <span style="color: #8c8c8c; font-size: larger">
          <v-icon color="#8c8c8c">group</v-icon>
          Organisations
        </span>
        <v-btn x-small
               color="#ff9800"
               rounded
               style="float: right;"
               id="create_org_btn"
        @click="newOrganisationDialog">+ create</v-btn>
        <v-list :expand="true" nav>

        <template  v-for="(item, i) in computedOrganisationItems">
          <base-item
              :id="`item-${i}`"
              :key="`item-${i}`"
              :item="item"
              color="primary"
              class="ma-0"
          />
        </template>
      </v-list>
        <span v-if="organisationItems.length === 0" style="font-size: 1rem; font-weight: 400; line-height: 1rem; color: #2d4470; padding-left: 18px;">No organisations yet</span>
        <v-divider style="width: 90%; margin: 5px 0px 5px 0px"/>
        <span style="color: #8c8c8c; font-size: larger">
          <v-icon color="#8c8c8c">settings</v-icon>
          Settings
        </span>
        <v-list  nav>
        <template  v-for="(item, i) in computedSettingsItems">
          <base-item
              :id="`menu-item-${item.title.toLowerCase()}`"
              :key="`item-${i}`"
              :item="item"
              color="primary"
              class="ma-0"
              value="user_context"
          />
        </template>
      </v-list>
      </v-card>
      <v-card
        :class="'mt-auto'"
        class="pa-2"
        :outlined="true"
        tile>
        <sidebar-footer sidebarType="user" />
      </v-card>
    </v-card>
  </div>
  </v-navigation-drawer>
</template>

<script>
import Item from '@/admin/components/base/Item'
import { mapState } from 'vuex'
import OrganisationForm from '@/organisation/components/OrganisationForm'
import ProjectForm from '@/components/ProjectForm'
import SideBarFooter from '@/components/SideBarFooter'
import OrganisationsMixin from '@/mixins/Organisation'
import MerginAPI from '@/mixins/MerginAPI'

export default {
  name: 'SideBar',
  components: {
    'base-item': Item,
    'sidebar-footer': SideBarFooter
  },
  mixins: [OrganisationsMixin, MerginAPI],
  props: {
    expandOnHover: {
      type: Boolean,
      default: false
    }
  },

  data () {
    return {
      items: [
        {
          title: 'My projects',
          to: '/projects/created'
        },
        {
          title: 'Shared with me',
          to: '/projects/shared'
        },
        {
          title: 'Explore',
          to: '/projects/explore'
        }
      ]
    }
  },
  computed: {
    ...mapState(['app', 'barColor', 'barImage', 'organisations']),
    username () {
      return this.$route.params.name
    },
    drawer: {
      get () {
        return this.$store.state.drawer
      },
      set (val) {
        this.$store.commit('SET_DRAWER', val)
      }
    },
    computedItems () {
      return this.items.map(this.mapItem)
    },
    computedOrganisationItems () {
      return this.organisationItems.map(this.mapItem)
    },
    computedSettingsItems () {
      return this.settingItems.map(this.mapItem)
    },
    profile () {
      return {
        avatar: true,
        title: this.$t('avatar'),
        username: this.app.user.username
      }
    },
    settingItems () {
      const items = []
      this.$router.getRoutes().filter(route => route.path.includes('/users/') && route.meta.toSidebar).forEach(item => {
        items.push(
          {
            title: item.meta.name,
            to: item.path.replace(':name', this.app.user.username)
          })
      })
      return items
    },
    organisationItems () {
      const userOrgs = []
      if (this.app.user.profile && this.app.user.profile.organisations) {
        Object.keys(this.app.user.profile.organisations).forEach(organisation => {
          const org = {
            title: organisation,
            to: `/organisations/${organisation}/projects`
          }
          userOrgs.push(org)
        })
      }
      return userOrgs
    },
    userProfile () {
      return this.app.user.profile
    },
    usage () {
      return this.userProfile.disk_usage / this.userProfile.storage
    }
  },
  methods: {
    mapItem (item) {
      return {
        ...item,
        children: item.children ? item.children.map(this.mapItem) : undefined
      }
    },
    newOrganisationDialog () {
      const props = { organisation: {} }
      const dialog = { maxWidth: 500, persistent: true }
      const listeners = {
        success: () => {
          this.getUserOrganisations()
          this.fetchUserProfile(this.app.user.username) // we load orgs in sidebar from user.profile
          this.$router.push({ name: 'user_organisations', params: { name: this.app.user.username } })
        }
      }
      this.$dialog.show(OrganisationForm, { props, listeners, dialog })
    },
    newProjectDialog () {
      // this.$gtm.trackEvent({
      //   event: null, // Event type [default = 'interaction'] (Optional)
      //   category: 'Test',
      //   action: 'click',
      //   label: 'new_project',
      //   noninteraction: false // Optional
      // })
      const dialog = { maxWidth: 500, persistent: true }
      this.$dialog.show(ProjectForm, { dialog })
    }
  }
}
</script>

<style lang="sass" scoped>
  @import '~vuetify/src/styles/tools/_rtl.sass'
  .primary.v-list-item--active.v-list-item
    background-color: #b0b1b5 !important

  .theme--dark.v-navigation-drawer
    background-color: #eaebef !important

  .theme--dark.v-navigation-drawer .v-divider
    border-color: hsl(240, 2%, 55%)

  .theme--dark.v-card
    background-color: #eaebef !important

  .v-application .white--text
    color: #2D4470 !important
    caret-color: #2D4470 !important

  .theme--dark.v-list-item:not(.v-list-item--active):not(.v-list-item--disabled)
     color: #2D4470 !important

  .v-list-item--link:hover
    background: rgba(0, 0, 0, 0.04) !important

  .theme--dark.v-card.v-list-item.v-list-item--link
      min-height: 20px !important
      padding: 5px 0px 5px 0px !important

  .truncate
    width: 100px
    white-space: nowrap
    overflow: hidden
    text-overflow: ellipsis

  .v-list
  ::v-deep .v-list-item
    font-size: 14px
    color: #444
    min-height: 32px
    .v-list-item__content
      padding: 0px 0px 0px 0px

  a
    text-decoration: none
    margin-top: 5px
</style>
