# Copyright (C) 2018 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

<template>
  <v-layout row justify-center align-start fill-height my-1>
    <slot name="left">
      <v-spacer class="hidden-md-and-down"/>
    </slot>
    <slot/>
    <slot name="right">
      <v-spacer class="hidden-md-and-down"/>
    </slot>
    <p class="version hidden-md-and-down">
      Version: {{ app.version }}
    </p>
  </v-layout>
</template>

<script>

export default {
  components: { },
  computed: {
    app () {
      return this.$store.state.app
    }
  }
}
</script>

<style lang="scss" scoped>
.version {
  position: absolute;
  right: 0;
  bottom: 0;
  margin: 0.25em 0.5em;
  opacity: 0.75;
  font-size: 12px;
}

::v-deep .main-content {
  width: 800px;
  margin: 0 1em;
  @media (max-width: 1264px) {
    width: 100%;
  }
}
</style>
