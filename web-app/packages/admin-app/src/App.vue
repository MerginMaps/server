<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <v-app :class="`${loggedUser ? 'appFont' : ''}`">
    <check-for-updates />
    <dialog-windows />
    <v-layout column fill-height>
      <transition name="fade">
        <router-view name="header" />
      </transition>
      <transition name="fade">
        <router-view :key="$route.fullPath" name="sidebar" />
      </transition>
      <v-card
        v-if="pingData && pingData.maintenance"
        outlined
        class="maintenance_warning"
      >
        <v-card-text>
          <b
            >The service is currently in read-only mode for maintenance. Upload
            and update functions are not available at this time. Please try
            again later.</b
          >
        </v-card-text>
      </v-card>
      <global-warning
        v-if="loggedUser"
        class="white--text"
        style="margin: auto"
      ></global-warning>
      <v-layout column fill-height class="app-content">
        <transition name="fade">
          <router-view class="page" />
        </transition>
      </v-layout>
    </v-layout>
    <!--    <upload-progress />-->
    <notifications />
  </v-app>
</template>

<script lang="ts">
import { CheckForUpdates } from '@mergin/admin-lib'
import {
  DialogWindows,
  GlobalWarning,
  initCsrfToken,
  initRequestInterceptors,
  initResponseInterceptors,
  Notifications,
  useAppStore,
  useInstanceStore,
  useNotificationStore,
  useUserStore
  // UploadProgress
} from '@mergin/lib'
import { mapActions, mapState } from 'pinia'
import { defineComponent } from 'vue'

export default defineComponent({
  name: 'app',
  components: {
    /* UploadProgress, */ Notifications,
    DialogWindows,
    GlobalWarning,
    CheckForUpdates
  },
  metaInfo() {
    return {
      title: 'Mergin Maps',
      meta: [
        {
          name: 'description',
          content:
            'Store and track changes to your geo-data. Mergin Maps is a repository of geo-data for collaborative work.'
        },
        {
          property: 'og:title',
          content:
            'Store and track changes to your geo-data. Mergin Maps is a repository of geo-data for collaborative work.'
        },
        { property: 'og:site_name', content: 'Mergin Maps' }
      ]
    }
  },
  computed: {
    ...mapState(useInstanceStore, ['pingData']),
    ...mapState(useUserStore, ['loggedUser']),
    ...mapState(useAppStore, ['serverError']),

    error() {
      return this.serverError
    }
  },
  watch: {
    error() {
      if (!this.error) return
      this.notificationError({ text: this.error })
      this.setServerError(null) // reset error so it is displayed just once
    },
    async loggedUser(value, oldValue) {
      if (value && value?.id !== oldValue?.id) {
        // here is reloaded current workspace if user has changed
        await this.checkCurrentWorkspace()
      }
    }
  },
  async created() {
    // App initialization
    const response = await this.initApp()
    initCsrfToken(response)
    await this.fetchConfig()
    if (this.loggedUser) {
      // here is loaded current workspace on startup (and reloaded in watcher when user has changed)
      await this.checkCurrentWorkspace()
    }

    const pingDataResponse = await this.fetchPing()
    const getIsMaintenance = () => {
      return pingDataResponse && pingDataResponse.maintenance
    }

    const resetUser = () => {
      if (this.loggedUser) {
        this.updateLoggedUser({ loggedUser: null })
      }
    }

    initRequestInterceptors(getIsMaintenance, ['/app/admin/login'])
    initResponseInterceptors(resetUser)
  },
  methods: {
    ...mapActions(useInstanceStore, ['fetchPing', 'initApp', 'fetchConfig']),
    ...mapActions(useNotificationStore, { notificationError: 'error' }),
    ...mapActions(useUserStore, ['checkCurrentWorkspace', 'updateLoggedUser']),
    ...mapActions(useAppStore, ['setServerError'])
  }
})
</script>

<style lang="scss">
@import url('https://fonts.googleapis.com/css2?family=Inter&display=swap');
html,
body,
.v-application {
  height: 100%;
  overflow: hidden !important;
  font-size: 14px;
}

.appFont {
  font-family: Inter, sans-serif;
}

.app-content {
  position: relative;
}

a {
  outline: none;
}

h3 {
  color: #2d052d;
}

.fade-leave-active {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.25s;
}

.fade-enter,
.fade-leave-to {
  opacity: 0;
}

.v-data-table {
  .v-data-table__wrapper {
    table {
      tbody {
        tr {
          td {
            font-size: 13px;
          }
        }
      }
    }
  }
}

.maintenance_warning {
  margin: auto;
  width: 100%;
  background-color: orange !important;
  color: rgba(0, 0, 0, 0.87) !important;
  padding-left: 400px;
  text-align: center;
  @media (max-width: 960px) {
    padding-left: 40px;
  }
}

.v-data-table {
  .v-data-table__wrapper {
    table {
      thead {
        tr {
          th {
            font-weight: 500;
            font-size: 12px;
          }
        }
      }
    }
  }
}

.v-btn.v-size--default {
  font-size: 14px;
  font-weight: 400;
}

.theme--light.v-data-table {
  margin: 0.5em 0;
  border: 1px solid #ddd;
  border-radius: 3px;
  padding: 0.5em;
  background-color: #f9f9f9;
}

.v-card__subtitle,
.v-card__text {
  font-size: 13px;
}

.v-btn {
  margin: 6px 8px 6px 8px;
  text-transform: capitalize;
}

.v-list-item--link::before {
  background-color: transparent;
}

.v-list-item--link:hover {
  background: rgba(0, 0, 0, 0.04);
}

.v-list-item--active {
  color: #2d052d !important;
}

.v-list--dense .v-list-item {
  min-height: 20px;
}

.v-list-item.v-list-item__content.v-list-item__title {
  font-weight: 300;
}

.theme--light.v-btn:not(.v-btn--flat):not(.v-btn--text):not(.v-btn--outlined) {
  background-color: #f5f5f5;
}

.theme--light.v-btn:not(.v-btn--flat):not(.v-btn--text):not(.v-btn--outlined):hover {
  background-color: #999;
}

.theme--light.v-input:not(.v-input--is-disabled) input,
.theme--light.v-input:not(.v-input--is-disabled) textarea {
  color: rgba(0, 0, 0, 0.87);
}

.v-table tr {
  color: #555;
}

.v-label::first-letter {
  text-transform: uppercase;
}

.v-label {
  min-width: 50px;
}
/*
  removing negative margin after upgrade vuetify from v2.3 to v2.4
  @see: https://github.com/vuetifyjs/vuetify/issues/12848#issuecomment-828408183
  .row:not([class*='my-']):not([class*='ma-']):not([class*='mt-']):not([class*='mb-']) {

  .row:not([class*='my-']):not([class*='ma-']):not([class*='mt-'])
  + .row:not([class*='my-']):not([class*='ma-']):not([class*='mt-']) {
*/
.row {
  margin-top: 0;
  margin-bottom: 0;
}

.blueButton {
  background-color: #2d4470 !important;
}

.row + .row {
  margin-top: 0;
}
</style>

<style lang="scss" scoped>
.layout.fill-height {
  overflow: hidden;
  min-height: 0;
}
</style>
