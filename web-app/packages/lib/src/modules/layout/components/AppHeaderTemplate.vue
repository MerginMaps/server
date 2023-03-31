<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <v-layout
    class="row shrink align-end justify-center header"
    v-bind:class="{ primary: isPrimary }"
  >
    <v-layout class="content">
      <router-link class="logo" :to="{ name: 'home' }">
        <img src="@/assets/MM_logo_HORIZ_NEG_color.svg" alt="Mergin logo" />
      </router-link>

      <slot name="menu">
        <v-btn
          class="mr-3 toggle-toolbar small-screen"
          elevation="1"
          fab
          small
          @click="setDrawer({ drawer: !drawer })"
        >
          <v-icon v-if="drawer" class="primary--text">
            fa-angle-double-left
          </v-icon>
          <v-icon v-else class="primary--text"> fa-angle-double-right</v-icon>
        </v-btn>
        <v-spacer />
      </slot>
      <v-menu
        v-if="loggedUser && loggedUser.email"
        :min-width="150"
        bottom
        left
        offset-y
        origin="top right"
        transition="scale-transition"
        id="user-menu"
      >
        <template v-slot:activator="{ on }">
          <v-btn
            v-on="on"
            text
            dark
            :ripple="false"
            class="icon-btn"
            cy-data="app-header-btn"
          >
            <div class="mr-2" style="position: relative; align-self: flex-end">
              <v-icon size="35">account_circle</v-icon>
              <slot name="invitationsIcon"></slot>
            </div>
            <div class="accountWrapper">
              <div class="accountNameWrapper">
                <span class="accountName font-weight-bold">
                  {{ getUserFullName }}
                </span>
                <v-icon small>keyboard_arrow_down</v-icon>
              </div>
              <div v-if="renderNamespace" class="namespace font-weight-bold">
                {{ currentNamespace || 'no workspace' }}
              </div>
            </div>
          </v-btn>
        </template>

        <v-list dense>
          <v-list-item class="pb-1">
            <div class="user-name">
              <strong> {{ getUserFullName }} </strong>
              <span class="caption"> {{ this.loggedUser.email }} </span>
            </div>
          </v-list-item>
          <v-divider class="mx-4 my-1"></v-divider>
          <v-list-item
            :to="{
              name: 'user_profile',
              params: { name: loggedUser.username }
            }"
            cy-data="app-header-profile"
            class="menuItemProfile"
          >
            Your Profile
          </v-list-item>
          <v-list-item @click="logout" cy-data="app-header-logout">
            <span class="menuItem"> Sign Out </span>
          </v-list-item>
          <slot name="menuItems"></slot>
        </v-list>
      </v-menu>
    </v-layout>
  </v-layout>
</template>

<script lang="ts">
import Vue from 'vue'
import { mapState, mapMutations, mapGetters } from 'vuex'

import { UserApi } from '@/modules/user/userApi'

export default Vue.extend({
  name: 'app-header-template',
  props: {
    isPrimary: {
      type: Boolean,
      default: true
    },
    renderNamespace: {
      type: Boolean,
      default: true
    }
  },
  computed: {
    ...mapState('layoutModule', ['drawer']),
    ...mapState('userModule', ['loggedUser']),
    ...mapGetters('userModule', ['getUserFullName']),
    ...mapState('projectModule', ['currentNamespace']),
    profileUrl() {
      return {
        name: 'user',
        params: { username: this.loggedUser?.username }
      }
    }
  },
  methods: {
    ...mapMutations('layoutModule', ['setDrawer']),
    async logout() {
      try {
        await UserApi.logout()
        if (this.$route.path === '/') {
          location.reload()
        } else {
          location.href = '/'
        }
      } catch (e) {
        console.log(e)
      }
    }
  }
})
</script>

<style lang="scss" scoped>
.header {
  padding: 0 0.5em;
  position: relative;
  min-height: 63px;
  flex-shrink: 0;
  z-index: 7;

  .content {
    height: 63px;
    align-items: center;
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

  .accountWrapper {
    display: flex;
    flex-direction: column;
  }

  .accountNameWrapper {
    display: flex;
    flex-direction: row;
  }

  .accountName {
    flex: 1;
    text-align: left;
    align-self: center;
    font-size: 12px;
  }

  .namespace {
    font-size: 12px;
    margin-right: 5px;
    text-align: left;
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
    }
  }
}

.user-name {
  display: flex;
  flex-direction: column;
}

@media (min-width: 960px) {
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

.menuItemProfile {
  padding-top: 5px;
}

.menuItem {
  padding-top: 5px;
  padding-bottom: 5px;
}

.menu-sub-content:hover,
.pointer:hover {
  opacity: 0.5;
}

.pointer {
  cursor: pointer;
}

.icon-btn:before {
  display: none;
}
</style>
