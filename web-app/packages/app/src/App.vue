<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <div class="grid min-h-screen">
    <dialog-windows />
    <router-view
      name="sidebar"
      v-slot="{ Component, route }"
      :key="$route.fullPath"
    >
      <transition name="fade">
        <div :key="route.name">
          <component :is="Component" />
        </div>
      </transition>
    </router-view>

    <main
      :class="[
        'surface-ground',
        'transition-all',
        'transition-duration-500',
        'col-12',
        'min-h-full',
        'overflow-auto',
        drawer && !isOverlay && 'xl:col-offset-2 xl:col-10',
      ]"
    >
      <router-view name="header" v-slot="{ Component, route }">
        <transition name="fade">
          <div :key="route.name">
            <component :is="Component" />
          </div>
        </transition>
      </router-view>
      <v-card
        v-if="pingData && pingData.maintenance"
        variant="outlined"
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
      <router-view class="page" v-slot="{ Component, route }">
        <transition name="fade">
          <div :key="route.name">
            <component :is="Component" />
          </div>
        </transition>
      </router-view>
    </main>
    <upload-progress />
    <notifications />
  </div>
</template>

<script lang="ts">
import {
  DialogWindows,
  GlobalWarning,
  initRequestInterceptors,
  initResponseInterceptors,
  Notifications,
  UploadProgress,
  useAppStore,
  useInstanceStore,
  useLayoutStore,
  useNotificationStore,
  useUserStore
} from '@mergin/lib'
import { mapActions, mapState } from 'pinia'
import { defineComponent } from 'vue'
import { useMeta } from 'vue-meta'

export default defineComponent({
  name: 'app',
  components: { UploadProgress, Notifications, DialogWindows, GlobalWarning },
  computed: {
    ...mapState(useInstanceStore, ['pingData']),
    ...mapState(useAppStore, ['serverError']),
    ...mapState(useUserStore, ['loggedUser']),
    ...mapState(useLayoutStore, ['drawer', 'isOverlay']),

    error() {
      return this.serverError
    }
  },
  watch: {
    error() {
      if (!this.error) return
      this.notificationError({
        text: this.error
      })
      this.setServerError(null) // reset error so it is displayed just once
    },
    async loggedUser(value, oldValue) {
      if (value && value?.id !== oldValue?.id) {
        // here is reloaded current workspace if user has changed
        await this.checkCurrentWorkspace()
      }
    }
  },
  setup() {
    useMeta({
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
    })
  },
  async created() {
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

    initRequestInterceptors(getIsMaintenance, [
      '/project/by_names',
      '/app/auth/login'
    ])
    initResponseInterceptors(resetUser)
  },
  methods: {
    ...mapActions(useAppStore, ['setServerError']),
    ...mapActions(useInstanceStore, ['fetchPing', 'fetchConfig', 'initApp']),
    ...mapActions(useNotificationStore, { notificationError: 'error' }),
    ...mapActions(useUserStore, ['checkCurrentWorkspace', 'updateLoggedUser'])
  }
})
</script>

<style lang="scss">

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

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
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
</style>
