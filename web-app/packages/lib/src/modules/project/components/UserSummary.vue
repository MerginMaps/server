<template>
  <div class="flex align-items-center w-full">
    <PAvatar
      :label="$filters.getAvatar(user.email, user.username)"
      size="large"
      shape="circle"
      :pt="{
        root: {
          class: 'mr-2 text-color-forest font-semibold flex-shrink-0',
          style: { borderRadius: '50%' }
        }
      }"
    />

    <div class="flex flex-column justify-content-between">
      <p class="title-t4 overflow-wrap-anywhere">
        {{
          user.fullname
            ? `${user.fullname} (${user.username})`
            : user.username
        }}
      </p>

      <p class="paragraph-p6 overflow-wrap-anywhere font-normal">
        {{ user.email }}
        <template v-if="isMe"> (me)</template>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { PropType } from 'vue'

import { ProjectCollaborator } from '../types'

defineProps({
  user: Object as PropType<ProjectCollaborator>,
  isMe: {
    type: Boolean,
    default: false
  }
})
</script>
