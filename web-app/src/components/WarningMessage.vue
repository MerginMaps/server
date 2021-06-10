<template>
  <v-card
    class="bubble mt-3"
      style="background-color: orange; color: rgba(0,0,0,.87);"
      outlined
      v-if="text">
    <span style="margin-left: 10px;"> {{text}}</span>
  </v-card>
</template>

<script>
export default {
  name: 'WarningMessage',
  props: {
    text: null
  }
}
</script>

<style scoped>
</style>
