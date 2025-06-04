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
        <CheckForUpdates />
        <transition name="fade">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
    <notifications />
  </div>
</template>

<script lang="ts">
import { CheckForUpdates } from '@mergin/admin-lib'
import {
  InstanceMaintenanceMessage,
  DialogWindows,
  initRequestInterceptors,
  initResponseInterceptors,
  Notifications,
  useAppStore,
  useInstanceStore,
  useNotificationStore,
  useUserStore,
  useLayoutStore,
  useProjectStore,
  useRouterTitle
} from '@mergin/lib'
import { mapActions, mapState } from 'pinia'
import { useToast } from 'primevue/usetoast'
import { defineComponent, watchEffect } from 'vue'
import { useMeta } from 'vue-meta'

export default defineComponent({
  name: 'app',
  components: {
    Notifications,
    DialogWindows,
    InstanceMaintenanceMessage,
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
  setup() {
    const { title } = useRouterTitle({
      defaultTitle: 'Mergin Maps Admin Panel'
    })
    useMeta({
      title: 'Mergin Maps Admin Panel',
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
    watchEffect(() => {
      document.title = title.value
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
      return pingDataResponse?.data?.maintenance
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
.fade-enter-active {
  transition: opacity ease-in 0.25s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
