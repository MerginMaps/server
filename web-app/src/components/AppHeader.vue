# Copyright (C) 2018 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

<template>
  <v-layout class="row shrink align-end justify-center header" v-bind:class="{ primary: isPrimary }">
    <v-layout class="content">
      <router-link
        class="logo"
        :to="{name: 'about'}">
        <img src="@/assets/logo.svg">
        <div class="banner" v-if="app.in_beta">BETA</div>
      </router-link>

      <slot name="menu">
         <v-btn
        class="mr-3 toggle-toolbar small-screen"
        elevation="1"
        fab
        small
        @click="setDrawer(!drawer)"
      >
        <v-icon v-if="drawer" class="primary--text">
          fa-angle-double-left
        </v-icon>
        <v-icon v-else class="primary--text">
          fa-angle-double-right
        </v-icon>
      </v-btn>
        <v-spacer/>
      </slot>
      <v-menu
        v-if="app.user && app.user.email"
        :min-width="150"
        bottom
        left
        offset-y
        origin="top right"
        transition="scale-transition"
        id="user-menu"
      >
        <template v-slot:activator="{ on }">
        <v-btn v-on="on" text dark :ripple="false" class="icon-btn">
          <v-icon class="mr-2">account_circle</v-icon><v-icon >arrow_drop_down</v-icon>
        </v-btn>
                  </template>

        <v-list dense>
          <v-list-item>
            <strong> {{ app.user.username }} </strong>
          </v-list-item>
          <v-divider></v-divider>
          <v-list-item :to="{ name: 'profile', params: { name: app.user.username }}">
            Your Profile
          </v-list-item>
          <v-divider ></v-divider>
          <v-list-item @click="logout">
            Sign Out
          </v-list-item>
        </v-list>
      </v-menu>
    </v-layout>
  </v-layout>
</template>

<script>
import OrganisationMixin from '../mixins/Organisation'
import { mapState, mapMutations } from 'vuex'

export default {
  name: 'app-header',
  props: {
    isPrimary: {
      type: Boolean,
      default: true
    }
  },
  mixins: [OrganisationMixin],
  computed: {
    ...mapState(['organisations', 'drawer']),
    app () {
      return this.$store.state.app
    },
    organisations () {
      return this.$store.state.organisations
    },
    namespace () {
      return this.$store.state.namespace
    },
    profileUrl () {
      return { name: 'user', params: { username: this.app.user.username } }
    }
  },
  created () {
    if (this.app.user) {
      // to have all available namespace for project creation
      this.getUserOrganisations()
    }
  },
  methods: {
    ...mapMutations({
      setDrawer: 'SET_DRAWER'
    }),
    logout () {
      this.$http.get('/auth/logout').then(() => {
        if (this.$route.path === '/') {
          location.reload()
        } else {
          location.href = '/'
        }
      })
    },
    clearUserData () {
      this.$store.dispatch('clearUserData')
    }
  }
}
</script>

<style lang="scss" scoped>
.header {
  padding: 0 0.5em;
  position: relative;
  min-height: 50px;
  flex-shrink: 0;
  z-index: 7;
  .content {
    height: 50px;
    align-items: flex-end;
  }
  .v-btn:hover:before {
    background-color: #fff;
  }
  .v-btn:before {
    background-color: transparent;
  }
  .v-btn {
    letter-spacing: normal;
  }

  a {
    color: #fff;
    min-width: 2em;
    margin: 0.35em 0.25em;
    padding: 0.35em 0.75em;
    text-decoration: none;
    font-weight: 500;
    /*font-size: 110%;*/
    font-size: 15.4px;
    &.active {
      color: orange;
    }
    &.logo {
      padding: 0;
      margin: 0 1em;
      height: inherit;
      position: relative;
      img {
        height: inherit;
        width: auto;
        padding: 0.25em 0;
      }
      .banner {
        position: absolute;
        top: 7px;
        left: 2px;
        color: orange;
        font-size: 10px;
        font-weight: 600;
      }
    }
  }
}
@media (min-width : 960px) {
  .small-screen {
    display: none;
  }
}
.v-btn {
  text-transform: none;
}
.menu-sub-title {
  font-weight: 700 !important;
}
.menu-sub-content {
  padding-left: 16px;
  cursor: pointer;
  width: 100%;
}
.menu-sub-content:hover,.pointer:hover {
  opacity: 0.5;
}
.pointer {
  cursor: pointer;
}
  .icon-btn:before {
    display: none;
  }
</style>
