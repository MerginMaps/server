# Copyright (C) 2018 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

<template>
  <div class="registration-window">
    <img class="bg" :src="require('@/assets/bg_grid.svg')"/>
    <v-spacer/>
    <v-layout justify-center align-end shrink>
      <v-img
        contain
        max-width="300"
        position="center bottom"
        :transition="false"
        :src="require('@/assets/img6.png')"
      />
    </v-layout>
    <v-container class="py-1">
      <v-card>
        <v-responsive class="mt-2">
          <img src="../assets/logo_color.svg" @click="$router.push('/login')">
        </v-responsive>
        <v-card-title class="primary--text font-weight-bold pb-0 ml-3">
          <h3> Create your account</h3>
          <v-spacer/>
            <v-btn
            text
            color="primary"
            class="reset"
            :to="{name: 'login'}"
            >Sign in
          </v-btn>
        </v-card-title>
        <v-card-text>
          <sign-up-form class="sign-up layout column" @success="redirect" />
        </v-card-text>
      </v-card>
    </v-container>
    <v-spacer/>
    <v-spacer/>
  </div>
</template>

<script>
import SignUpForm from '@/components/SignUpForm'
import VueRouter from 'vue-router'
const { isNavigationFailure, NavigationFailureType } = VueRouter


export default {
  name: 'Registration',
  components: { SignUpForm },
  methods: {
    redirect () {
      if (this.$route.query.redirect) {
        this.$router.push(this.$route.query.redirect).catch(e => {
          if (isNavigationFailure(e, NavigationFailureType.redirected)) {
            // expected redirect
            //   https://router.vuejs.org/guide/advanced/navigation-failures.html#detecting-navigation-failures
          } else {
            this.$notification.error(e)
          }
        })
      } else {
        this.$router.push({ name: 'my_projects' })
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.registration-window {
  position: fixed;
  top: 0;
  left: 0;
  height: 100%;
  width: 100%;

  background-image: linear-gradient(#172238, #2c436f);
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

  ::v-deep .v-card {
    max-width: 500px;
    flex: 1;
    opacity: 0.9;

    .v-responsive__content {
      display: flex;
      flex-direction: row;
      justify-content: center;
      margin-top: 0.25em;
      cursor: pointer;
      img {
        height: 4em;
        width: auto;
      }
    }

    .v-card__text {
      display: flex;
      flex-direction: column;
    }

  }
  ::v-deep .v-btn {
    text-transform: none;
    &.reset {
      align-self: center;
    }
  }
}
</style>
