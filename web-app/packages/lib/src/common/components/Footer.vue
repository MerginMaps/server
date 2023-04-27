<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <section class="footer py-4">
    <v-layout row wrap align-center>
      <v-row>
        <v-col xs12 sm6 px-4 text-xs-center text-sm-left>
          <span
            >&copy; 2019-{{ new Date().getFullYear() }}
            <a href="https://www.lutraconsulting.co.uk/"
              >Lutra Consulting Limited</a
            >. All rights reserved.</span
          >
        </v-col>
        <v-col
          style="text-align: right"
          sm6
          text-sm-right
          xs12
          px-4
          :class="{
            'justify-center': $vuetify.display.xs,
            'justify-end': $vuetify.display.smAndUp
          }"
        >
          <a class="icon" href="https://github.com/lutraconsulting/">
            <v-icon>fab fa-github</v-icon>
          </a>
          <a class="icon" href="https://twitter.com/lutraconsulting/">
            <v-icon>fab fa-twitter</v-icon>
          </a>
          <a
            class="icon"
            href="https://www.linkedin.com/company/lutra-consulting"
          >
            <v-icon>fab fa-linkedin</v-icon>
          </a>
        </v-col>
      </v-row>
    </v-layout>
  </section>
</template>

<script lang="ts">
import { defineComponent } from 'vue'

export default defineComponent({
  name: 'Footer'
})
</script>

<style lang="scss" scoped>
.layout {
  width: 100%;
  max-width: 1140px;
}

.footer {
  background-color: #eaebef;
  max-height: 70px;

  a {
    text-decoration: none;

    &.icon:hover > i {
      color: #555;
    }
  }

  .icon {
    width: 1.5em;
    height: 1.5em;
    margin: 0.5em;
    color: grey;
  }
}
</style>
