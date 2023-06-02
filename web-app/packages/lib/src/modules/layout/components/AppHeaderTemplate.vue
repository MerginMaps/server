<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <v-app-bar
    flat
    class="header"
    v-bind:class="{ primary: isPrimary }"
    theme="dark"
  >
    <template #prepend
      ><slot name="menu">
        <!-- TODO: `fab` prop was removed, check if `rounded` prop is enough here -->
        <v-btn
          class="toggle-toolbar small-screen"
          elevation="1"
          rounded
          size="small"
          @click="setDrawer({ drawer: !drawer })"
        >
          <v-icon v-if="drawer" class="text-primary">
            fa-angle-double-left
          </v-icon>
          <v-icon v-else class="text-primary"> fa-angle-double-right</v-icon>
        </v-btn>
      </slot>
      <router-link class="logo" :to="{ name: 'home' }">
        <img
          src="@/assets/MM_logo_HORIZ_NEG_color.svg"
          alt="Mergin logo"
          :style="{ height: '63px' }"
        />
      </router-link>
    </template>

    <template #title></template>

    <template #append
      ><v-menu
        v-if="loggedUser && loggedUser.email"
        :min-width="150"
        location="bottom"
        start
        origin="top right"
        transition="scale-transition"
        id="user-menu"
      >
        <template v-slot:activator="{ props }">
          <v-btn
            v-bind="props"
            text
            theme="dark"
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
                <v-icon size="small">keyboard_arrow_down</v-icon>
              </div>
              <div v-if="renderNamespace" class="namespace font-weight-bold">
                {{ currentNamespace || 'no workspace' }}
              </div>
            </div>
          </v-btn>
        </template>

        <v-list density="compact">
          <v-list-item class="pb-1">
            <div class="user-name">
              <strong> {{ getUserFullName }} </strong>
              <span class="caption"> {{ loggedUser.email }} </span>
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
        </v-list> </v-menu
    ></template>
  </v-app-bar>
</template>

<script lang="ts">
import { mapActions, mapState, mapGetters } from 'pinia'
import { defineComponent } from 'vue'

import { useLayoutStore } from '@/modules/layout/store'
import { useProjectStore } from '@/modules/project/store'
import { useUserStore } from '@/modules/user/store'
import { UserApi } from '@/modules/user/userApi'

export default defineComponent({
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
    ...mapState(useLayoutStore, ['drawer']),
    ...mapState(useUserStore, ['loggedUser']),
    ...mapGetters(useUserStore, ['getUserFullName']),
    ...mapState(useProjectStore, ['currentNamespace']),
    profileUrl() {
      return {
        name: 'user',
        params: { username: this.loggedUser?.username }
      }
    }
  },
  methods: {
    ...mapActions(useLayoutStore, ['setDrawer']),

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
    text-decoration: none;
    &.logo {
      img {
        width: auto;
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
  margin: 0;
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
