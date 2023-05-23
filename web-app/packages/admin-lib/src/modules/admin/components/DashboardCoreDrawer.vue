<!--
Based on template:
Product Page: https://www.creative-tim.com/product/vuetify-material-dashboard
Copyright 2019 Creative Tim (https://www.creative-tim.com)

Modifications by:
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <v-navigation-drawer
    id="core-navigation-drawer"
    v-model="drawer"
    theme="light"
    :expand-on-hover="expandOnHover"
    :right="$vuetify.locale.isRtl"
    :src="barImage"
    mobile-breakpoint="960"
    app
    width="260"
    v-bind="$attrs"
  >
    <template v-slot:img="props">
      <v-img :gradient="`to bottom, ${barColor}`" v-bind="props" />
    </template>

    <v-divider class="mb-1" />

    <v-list dense nav>
      <v-list-item>
        <v-list-item-avatar
          class="align-self-center my-1"
          contain
          tile
          size="45"
        >
          <v-img
            :src="getImageUrl('mm-icon-white-large-no-transparency.png')"
            max-height="45"
          />
        </v-list-item-avatar>

        <v-list-item-content>
          <v-list-item-subtitle class="font-weight-bold"
            >Admin panel</v-list-item-subtitle
          >
          <v-list-item-title
            class="text-h6 font-weight-bold"
            v-text="username"
          />
        </v-list-item-content>
      </v-list-item>
    </v-list>

    <v-divider class="mb-2" />

    <v-list expand nav>
      <!-- Style cascading bug  -->
      <!-- https://github.com/vuetifyjs/vuetify/pull/8574 -->
      <div />

      <template v-for="(item, i) in computedItems" :key="`item-${i}`">
        <!--   TODO: handle item children (it is only in admin apps now)     -->
        <!--        <base-item-group v-if="item.children" :key="`group-${i}`" :item="item">-->
        <!--          &lt;!&ndash;  &ndash;&gt;-->
        <!--        </base-item-group>-->
        <!---->
        <!--        <base-item v-else :key="`item-${i}`" :item="item" />-->
        <base-item :item="item" color="black" />
      </template>

      <!-- Style cascading bug  -->
      <!-- https://github.com/vuetifyjs/vuetify/pull/8574 -->
      <div />
    </v-list>
  </v-navigation-drawer>
</template>

<script lang="ts">
// Utilities
import { BaseItem, useLayoutStore, useUserStore } from '@mergin/lib'
import { mapActions, mapState } from 'pinia'
import { defineComponent } from 'vue'

export default defineComponent({
  name: 'DashboardCoreDrawer',

  components: { BaseItem },

  props: {
    expandOnHover: {
      type: Boolean,
      default: false
    }
  },

  computed: {
    ...mapState(useLayoutStore, {
      drawerState: 'drawer',
      barColor: 'barColor',
      barImage: 'barImage'
    }),
    ...mapState(useUserStore, ['loggedUser']),

    drawer: {
      get() {
        return this.drawerState
      },
      set(val) {
        this.setDrawer({ drawer: val })
      }
    },
    items() {
      const items = [
        {
          title: 'Accounts',
          icon: 'mdi-account-multiple',
          to: '/accounts'
        },
        {
          title: 'Projects',
          icon: 'mdi-book-multiple',
          to: '/projects'
        }
      ]
      this.$router
        .getRoutes()
        .filter((route) => route.path.includes('/') && route.meta.toSidebar)
        .forEach((item) => {
          items.push({
            title: item.meta.name,
            to: item.path,
            icon: item.meta.icon
          })
        })
      items.push({
        title: 'Settings',
        icon: 'mdi-cog',
        to: '/settings'
      })
      return items
    },
    computedItems() {
      return this.items.map(this.mapItem)
    },
    username() {
      return (this.loggedUser?.username ?? 'Admin').toUpperCase()
    }
  },

  methods: {
    ...mapActions(useLayoutStore, ['setDrawer']),

    getImageUrl(name) {
      return new URL(`../../../assets/${name}`, import.meta.url).href
    },
    mapItem(item) {
      return {
        ...item,
        children: item.children ? item.children.map(this.mapItem) : undefined
        // title: this.$tm(item.title)
      }
    }
  }
})
</script>

<style lang="sass">
@use 'vuetify/tools'

#core-navigation-drawer .theme--dark.v-navigation-drawer
  background-color: #eaebef

#core-navigation-drawer
  .v-list-group__header.v-list-item--active:before
    opacity: .24

  .v-list-item
    &__icon--text,
    &__icon:first-child
      justify-content: center
      text-align: center
      width: 20px

      +tools.ltr()
        margin-right: 24px
        margin-left: 12px !important

      +tools.rtl()
        margin-left: 24px
        margin-right: 12px !important

  .v-list--dense
    .v-list-item
      &__icon--text,
      &__icon:first-child
        margin-top: 10px

  .v-list-group--sub-group
    .v-list-item
      +tools.ltr()
        padding-left: 8px

      +tools.rtl()
        padding-right: 8px

    .v-list-group__header
      +tools.ltr()
        padding-right: 0

      +tools.rtl()
        padding-right: 0

      .v-list-item__icon--text
        margin-top: 19px
        order: 0

      .v-list-group__header__prepend-icon
        order: 2

        +tools.ltr()
          margin-right: 8px

        +tools.rtl()
          margin-left: 8px
</style>
