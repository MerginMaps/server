<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <v-chip v-bind="$attrs" label :ripple="false">
    <v-avatar size="18" start>
      <send-icon
        v-if="isUserSearchInvite(item)"
        size="18"
        class="text-primary"
      />
      <user-icon v-else size="18" class="text-primary" />
    </v-avatar>
    {{ isUserSearchInvite(item) ? item.email : item.username }}
  </v-chip>
</template>

<script lang="ts">
import { defineComponent, PropType } from 'vue'
import { SendIcon, UserIcon } from 'vue-tabler-icons'

import {
  UserSearchInvite,
  UserSearch,
  isUserSearchInvite
} from '@/modules/user/types'

export default defineComponent({
  name: 'UserSearchChip',
  methods: { isUserSearchInvite },
  components: { SendIcon, UserIcon },
  props: {
    item: Object as PropType<UserSearch | UserSearchInvite>
  }
})
</script>

<style lang="scss" scoped></style>
