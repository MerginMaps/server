<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <v-chip v-bind="$attrs" v-on="$listeners" label :ripple="false">
    <v-avatar size="18" left>
      <send-icon v-if="item.isInvite" size="18" class="primary--text" />
      <user-icon v-else size="18" class="primary--text" />
    </v-avatar>
    {{ item.isInvite ? item.email : item.username }}
  </v-chip>
</template>

<script lang="ts">
import Vue, { PropType } from 'vue'
import { SendIcon, UserIcon } from 'vue-tabler-icons'

import { UserSearchInvite, UserSearch } from '@/modules/user/types'

export default Vue.extend({
  name: 'UserSearchChip',
  components: { SendIcon, UserIcon },
  props: {
    item: Object as PropType<UserSearch | UserSearchInvite>
  }
})
</script>

<style lang="scss" scoped></style>
