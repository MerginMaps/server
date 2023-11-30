<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <page-view
    v-if="loggedUser.username === name"
    :style="`padding-left: ${
      drawer ? 260 : 20
    }px; overflow-y: auto; padding-right:20px; margin-right: 0px;`"
  >
    <router-view />
  </page-view>
</template>

<script lang="ts">
import { mapState } from 'pinia'
import { defineComponent } from 'vue'

import PageView from '@/modules/layout/components/PageView.vue'
import { useLayoutStore } from '@/modules/layout/store'
import { useUserStore } from '@/modules/user/store'

export default defineComponent({
  name: 'RootView',
  components: {
    PageView
  },
  computed: {
    ...mapState(useLayoutStore, ['drawer']),
    ...mapState(useUserStore, ['loggedUser']),
    name() {
      return this.$route.params.name
    }
  }
})
</script>
