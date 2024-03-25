<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <!-- Tip from MM -->
  <div
    class="tip-message flex flex-column row-gap-2 md:flex-row align-items-center border-round-xl p-4"
  >
    <div class="md:mr-4">
      <slot name="image">
        <img src="@/assets/bulb.svg" aria-label="Bulb" />
      </slot>
    </div>

    <div class="text-center md:text-left">
      <p class="tip-message-title title-t3 mb-1">
        <slot name="title">Tip from Mergin Maps</slot>
      </p>
      <p class="opacity-80 paragraph-p5">
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
