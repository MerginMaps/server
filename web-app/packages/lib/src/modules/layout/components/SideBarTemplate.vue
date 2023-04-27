<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <v-navigation-drawer
    class="user-side-bar d-flex align-start flex-column mb-6"
    id="core-navigation-drawer-user"
    v-model="drawer"
    :expand-on-hover="expandOnHover"
    :right="$vuetify.locale.isRtl"
    mobile-breakpoint="960"
    :dark="barColor !== 'rgba(228, 226, 226, 1), rgba(255, 255, 255, 0.7)'"
    app
    width="200"
    v-bind="$attrs"
    v-if="loggedUser"
    data-cy="side-bar"
  >
    <div style="height: 100%">
      <v-card
        class="d-flex flex-column"
        flat
        tile
        style="height: 100%; width: 200px"
        :outlined="true"
      >
        <v-card class="pa-2" tile :outlined="true" style="margin-top: 40px">
          <slot name="items"></slot>
          <v-divider style="width: 90%; margin: 5px 0 5px 0" />
          <v-list nav flat>
            <side-bar-item
              id="item-userProfile"
              key="item-userProfile"
              :item="profileItem"
            >
              <template #icon>
                <component :is="profileItem.tablerIcon"></component>
              </template>
            </side-bar-item>
          </v-list>
        </v-card>
        <slot name="footer"></slot>
      </v-card>
    </div>
  </v-navigation-drawer>
</template>

<script lang="ts">
import { defineComponent } from 'vue'
import { UserIcon } from 'vue-tabler-icons'
import { mapState } from 'vuex'

import SideBarItem from '@/modules/layout/components/SideBarItem.vue'

export default defineComponent({
  name: 'SideBarTemplate',
  components: {
    SideBarItem,
    UserIcon
  },
  props: {
    expandOnHover: {
      type: Boolean,
      default: false
    }
  },
  data: function () {
    return {
      profileItem: {
        title: 'User profile',
        to: '/profile',
        tablerIcon: 'user-icon'
      }
    }
  },
  computed: {
    ...mapState('userModule', ['loggedUser']),
    ...mapState('layoutModule', {
      barColor: 'barColor',
      drawerState: 'drawer'
    }),
    drawer: {
      get() {
        return this.drawerState
      },
      set(val) {
        this.$store.commit('layoutModule/setDrawer', { drawer: val })
      }
    }
  },
  methods: {}
})
</script>

<style lang="scss" scoped>
.theme--dark.v-navigation-drawer {
  background-color: #eaebef !important;
}

.theme--dark.v-navigation-drawer .v-divider {
  border-color: #f3f4f8;
}

.theme--dark.v-card {
  background-color: #eaebef !important;
}

.v-application .white--text {
  color: #2d4470 !important;
  caret-color: #2d4470 !important;
}
</style>
