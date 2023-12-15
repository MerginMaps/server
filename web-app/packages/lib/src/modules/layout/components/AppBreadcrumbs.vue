<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <PBreadcrumb
    v-if="items.length > 0"
    :model="items"
    :pt="{
      root: {
        style: {
          backgroundColor: 'transparent'
        },
        class: 'border-none'
      }
    }"
  >
    <template #item="{ item, props }">
      <router-link
        v-if="item.route"
        v-slot="{ href, navigate }"
        :to="{
          params: item.params,
          name: item.route
        }"
        custom
      >
        <a :href="href" v-bind="props.action" @click="navigate">
          <span :class="[item.icon, 'text-color']" />
          <span
            :class="[
              'opacity-80 text-sm',
              item.active ? 'text-color-forest font-semibold' : 'text-color'
            ]"
            >{{ item.label }}</span
          >
        </a>
      </router-link>
    </template>
  </PBreadcrumb>
</template>

<script setup lang="ts">
import { MenuItem } from 'primevue/menuitem'
import { useRoute } from 'vue-router'

const route = useRoute()
const items: MenuItem[] = route.matched
  .filter((item) => item.meta.title)
  .map<MenuItem>((item) => ({
    label: item.meta.title,
    active: route.name === item.name,
    route: item.name,
    params: route.params
  }))
</script>

<style scoped lang="scss"></style>
