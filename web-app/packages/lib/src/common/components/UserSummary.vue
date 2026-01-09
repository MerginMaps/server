<template>
  <div class="flex align-items-center w-full">
    <PAvatar
      :label="$filters.getAvatar(email, fullName)"
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
        {{ fullName ? `${fullName} (${username})` : username }}
      </p>

      <p class="paragraph-p6 overflow-wrap-anywhere font-normal">
        {{ email }}
        <template v-if="isMe"> (me)</template>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  username: string
  email: string
  fullName?: string
  isMe?: boolean
}

defineProps<Props>()
</script>
