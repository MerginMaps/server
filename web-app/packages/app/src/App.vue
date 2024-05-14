<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <div class="grid grid-nogutter min-h-screen">
    <dialog-windows />
    <router-view name="sidebar" v-slot="{ Component }" :key="$route.fullPath">
      <component :is="Component" v-if="isSideBar" />
    </router-view>

    <main
      :class="[
        'surface-ground',
        'transition-all',
        'transition-duration-500',
        'min-h-full',
        'overflow-auto',
        'pb-4',
        isSideBar && drawer && !isUnderOverlayBreakpoint
          ? 'col-offset-2 col-10'
          : 'col-12'
      ]"
    >
      <router-view name="header" v-slot="{ Component, route }">
        <div :key="route.name">
          <component :is="Component" />
          <PDivider v-if="Component" class="m-0"></PDivider>
        </div>
      </router-view>
      <router-view v-slot="{ Component }">
        <instance-maintenance-message v-if="pingData && pingData.maintenance" />
        <transition name="fade">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
    <notifications />
  </div>
</template>

<script lang="ts">
import {
  DialogWindows,
  initRequestInterceptors,
  initResponseInterceptors,
  Notifications,
  UploadProgress,
  useAppStore,
  useInstanceStore,
  useLayoutStore,
  useNotificationStore,
  useUserStore,
  AppContainer,
  InstanceMaintenanceMessage,
useProjectStore
} from '@mergin/lib'
import { mapActions, mapState } from 'pinia'
import { useToast } from 'primevue/usetoast'
import { defineComponent } from 'vue'
import { useMeta } from 'vue-meta'

export default defineComponent({
  name: 'app',
  components: {
    UploadProgress,
    Notifications,
    DialogWindows,
    AppContainer,
    InstanceMaintenanceMessage
  },
  computed: {
    ...mapState(useInstanceStore, ['pingData']),
    ...mapState(useAppStore, ['serverError']),
    ...mapState(useUserStore, ['loggedUser']),
    ...mapState(useLayoutStore, ['drawer', 'isUnderOverlayBreakpoint']),

    error() {
      return this.serverError
    },

    /** Check if sidebar is occuring in route */
    isSideBar() {
      return (
        !!this.$route.matched.find((item) => item.components.sidebar) &&
        !!this.loggedUser?.id
      )
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
    const toast = useToast()
    const notificationStore = useNotificationStore()
    const layoutStore = useLayoutStore()
    const projectStore = useProjectStore()

    notificationStore.init(toast)
    layoutStore.init()
    projectStore.filterPermissions(['editor'], ['edit'])
  },
  async created() {
    await this.fetchConfig()
    if (this.loggedUser) {
      // here is loaded current workspace on startup (and reloaded in watcher when user has changed)
      await this.checkCurrentWorkspace()
    }

    const pingDataResponse = await this.fetchPing()
    const getIsMaintenance = () => {
      return pingDataResponse?.data?.maintenance
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
    ...mapActions(useNotificationStore, {
      notificationError: 'error'
    }),
    ...mapActions(useUserStore, ['checkCurrentWorkspace', 'updateLoggedUser'])
  }
})
</script>

<style lang="scss">
.fade-enter-active {
  transition: opacity ease-in 0.25s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
