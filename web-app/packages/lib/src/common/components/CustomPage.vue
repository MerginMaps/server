<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <div class="main-window">
    <v-layout justify-center align-end shrink>
      <v-img
        contain
        max-width="300"
        position="center bottom"
        :transition="false"
      />
    </v-layout>

    <v-container class="py-1">
      <div class="form-wrapper">
        <!-- slot for e.g. v-card in view component -->
        <slot />
      </div>
    </v-container>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue'

export default defineComponent({
  name: 'CustomPage'
})
</script>

<style lang="scss" scoped>
.main-window {
  font-family: Inter, sans-serif;
  position: fixed;
  justify-content: center;
  top: 0;
  left: 0;
  height: 100%;
  width: 100%;

  // TODO: linear-Gradient for Tomas
  background-image: linear-gradient(#eeeeee, #e6e6e6);
  display: flex;
  flex-direction: column;
  z-index: 100;
  overflow: auto;

  .bg {
    position: absolute;
    left: 0;
    top: 0;
    height: 100%;
    width: 100%;
    object-fit: cover;
  }

  .container {
    display: flex;
    align-items: center;
    justify-content: center;
    flex: 0 0 auto;
  }
  .form-wrapper {
    display: flex;
    background: linear-gradient(90deg, #2d052d 50%, #00a884 50%);
    box-shadow: 0 0.5rem 1rem 1px rgba(0, 0, 0, 0.45);
    //TODO: Size of padding for "purple and green" [] for Tomas
    border-radius: 5px;
    padding: 20px;
  }
  @media (max-width: 480px) {
    .form-wrapper {
      //TODO: Size of padding for "purple and green" [] for Tomas - mobile
      padding: 10px;
    }
  }
}
</style>
