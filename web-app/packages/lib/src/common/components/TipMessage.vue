<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <!-- Tip from MM -->
  <div class="tip-message flex align-items-center border-round-xl">
    <img src="@/assets/bulb.svg" aria-label="Bulb" class="p-4" />
    <div class="p-2">
      <p class="tip-message-title text-sm font-semibold">
        <slot name="title">Tip from Mergin Maps</slot>
      </p>
      <p class="opacity-80 text-sm line-height-4">
        <slot name="description"></slot>
      </p>
    </div>
  </div>
</template>

<style scoped lang="scss">
.tip-message {
  background-color: var(--light-green-color);
  &-title {
    color: var(--deep-ocean-color);
  }
}
</style>
