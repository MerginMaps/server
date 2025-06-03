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
        class: 'border-none p-2 w-full overflow-x-auto'
      }
    }"
  >
    <template #separator>
      <i class="ti ti-chevron-right" />
    </template>
    <template #item="{ item, props }">
      <router-link
        v-if="item.path"
        v-slot="{ href, navigate }"
        :to="{
          path: item.path
        }"
        custom
      >
        <a :href="href" v-bind="props.action" @click="navigate">
          <span :class="[item.icon, 'text-color']" />
          <span
            :class="[
              'opacity-80 paragraph-p5',
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
import { computed } from 'vue'
import { useRoute } from 'vue-router'

type EnhancedMenuItem = MenuItem & { path: string; active?: boolean }

const route = useRoute()

function parseBreadcrump(item: {
  title: string
  path: string
}): EnhancedMenuItem {
  return {
    label: item.title,
    path: item.path
  }
}

const matchedBreacrumps = computed(() => {
  return route.matched.reduce<EnhancedMenuItem[]>((acc, curr) => {
    if (curr.name === route.name) return acc
    const breadcrumps =
      typeof curr.meta?.breadcrump === 'function'
        ? curr.meta?.breadcrump(route)
        : curr.meta?.breadcrump
    return [...acc, ...(breadcrumps ?? []).map(parseBreadcrump)]
  }, [])
})

const currentRouteBreacrumps = computed(() => {
  const breadcrumps =
    typeof route.meta?.breadcrump === 'function'
      ? route.meta?.breadcrump(route)
      : route.meta?.breadcrump
  return (breadcrumps ?? []).map(parseBreadcrump)
})

// Merge all matched meta.breadcrumps with current route breadcrumps
const items = computed(() =>
  [
    ...matchedBreacrumps.value,
    // adding current route wich is not in matched meta
    ...currentRouteBreacrumps.value
  ]
    // last will be active
    .map((item, index, items) => ({
      ...item,
      active: index === items.length - 1
    }))
)
</script>

<style scoped lang="scss"></style>
