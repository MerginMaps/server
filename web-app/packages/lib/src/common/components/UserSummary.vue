<template>
  <div class="flex align-items-center w-auto">
    <PAvatar
      :label="$filters.getAvatar(email, name)"
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
        {{ name ? `${name} (${username})` : username }}
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
  name?: string
  isMe?: boolean
}

defineProps<Props>()
</script>
