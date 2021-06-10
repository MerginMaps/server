# Copyright (C) 2018 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

<template>
  <div class="login-window">
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
          <img src="../assets/logo_color.svg" @click="home">
        </v-responsive>
        <v-card-text>
          <p
            v-if="errorMsg"
            class="text-xs-center red--text"
            v-text="errorMsg"
          />
          <v-form class="login-form">
            <template v-if="forgotPassword">
              <v-text-field
                placeholder="Email"
                name="email"
                color="orange"
                v-model="email"
                :error-messages="errors.email"
                @keyup.enter="reset"
              />
              <v-btn
                :dark="email !== ''"
                color="orange"
                :disabled="!email"
                @click="reset"
              >
                Reset Password
              </v-btn>
            </template>
            <template v-else>
              <v-text-field
                placeholder="Username or email"
                name="login"
                color="orange"
                v-model="login"
                :error-messages="errors.login"
                @keyup.enter="loginUser"
              />
              <v-text-field
                placeholder="Password"
                name="password"
                color="orange"
                v-model="password"
                :append-icon="passwordVisible ? 'visibility_off' : 'visibility'"
                @click:append="passwordVisible = !passwordVisible"
                :type="passwordVisible ? 'text' : 'password'"
                :error-messages="errors.password"
                @keyup.enter="loginUser"
              />
              <v-btn
                :dark="Boolean(login && password)"
                :disabled="!login || !password"
                color="orange"
                class="mx-0 mt-3"
                id="login-btn"
                @click="loginUser"
              >
                Sign In
              </v-btn>
            </template>
          </v-form>
          <div class="d-flex justify-space-between">
            <v-btn
            v-if="!forgotPassword"
            text small
            color="primary"
            class="reset"
            :to="{name: 'login', params:{reset: 'reset'}}"
            >Forgot password?
          </v-btn>
            <v-btn
            v-if="!forgotPassword && app.registration"
            text small
            color="primary"
            class="reset"
            @click="toRegister"
            >Register
          </v-btn>
          </div>
        </v-card-text>
        <p class="cookies">This website uses cookies. By continuing to use this website you consent to their use.</p>
      </v-card>
    </v-container>
    <v-spacer/>
    <v-spacer/>
  </div>
</template>

<script>
import FormMixin from '@/mixins/Form'
import VueRouter from 'vue-router'
import MerginAPI from '@/mixins/MerginAPI'
const { isNavigationFailure, NavigationFailureType } = VueRouter

export default {
  mixins: [FormMixin, MerginAPI],
  data () {
    return {
      valid: true,
      login: '',
      password: '',
      email: '',
      passwordVisible: false
    }
  },
  created () {
    this.$store.commit('user', null) // clear current user to prevent commit to store (and thus reload)
  },
  computed: {
    app () {
      return this.$store.state.app
    },
    forgotPassword () {
      return this.$route.params.reset === 'reset'
    }
  },
  methods: {
    loginUser () {
      this.clearErrors()
      const data = {
        login: this.login.trim(),
        password: this.password.trim()
      }
      this.$http.post('/auth/login', data)
        .then((resp) => {
          this.$store.commit('user', resp.data)
          this.$emit('login')
          if (this.$route.query.redirect) {
            this.$router.push(this.$route.query.redirect).catch(e => {
              if (isNavigationFailure(e, NavigationFailureType.redirected)) {
                // expected redirect
                //   https://router.vuejs.org/guide/advanced/navigation-failures.html#detecting-navigation-failures
              } else {
                this.$notification.error(e)
              }
            })
          }
          if (this.$route.path === '/login') {
            this.$router.push({ name: 'dashboard' })
          }
        })
        .catch((err) => {
          this.handleError(err)
          this.errors.password = err.response.data.detail
        })
    },
    reset () {
      this.clearErrors()
      this.$http.post('/auth/password_reset', { email: this.email })
        .then(() => {
          this.forgotPassword = false
          this.$notification.show('Email with password reset link was sent to your email address', { timeout: 3000 })
        })
        .catch(err => this.handleError(err, 'Failed to send confirmation email'))
    },
    home () {
      this.$router.push('/')
    },
    toRegister () {
      if (!this.app.user) {
        this.$store.commit('guestUser')
      }
      this.$router.push('/register')
    }
  }
}
</script>

<style lang="scss" scoped>
.login-window {
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
    max-width: 400px;
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
    form {
      display: flex;
      flex-direction: column;
      input {
        padding-left: 0.25em;
      }
      .input-group label:after {
        /* Remove asterics from required fields */
        display: none;
      }
      .v-input__append-inner {
        position: absolute;
        right: 0.25em;
        .v-icon {
          color: #ccc!important;
        }
      }
    }
    .cookies {
      margin: 0.5em;
      text-align: center;
    }
    .version {
      margin: 1em 0 0.5em 0;
      text-align: center;
      opacity: 0.6;
      font-size: 90%;
    }
  }
  .copyright {
    position: absolute;
    right: -1em;
    bottom: 0.25em;
    padding: 0 2em 0 2em;
    color: #fff;
    text-shadow: 1px 1px 3px #333;
    opacity: 0.7;
    user-select: none;
    b {
      font-weight: 500;
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
