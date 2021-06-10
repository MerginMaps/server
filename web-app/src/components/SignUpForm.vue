# Copyright (C) 2018 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

<template>
  <v-card-text class="pb-1">
    <p
      v-if="errorMsg"
      class="text-xs-center red--text"
      v-text="errorMsg"
    />
    <v-form class="layout column sign-up-form">
      <v-text-field
        placeholder="Username"
        name="username"
        color="orange"
        v-model="username"
        :error-messages="errors.username"
      />
     <v-text-field
        placeholder="Email"
        name="email"
        color="orange"
        v-model="email"
        :error-messages="errors.email"
      />
        <v-layout align-center>
          <v-text-field
              placeholder="Password"
              name="password"
              color="orange"
              v-model="password"
              :append-icon="passwordVisible ? 'visibility_off' : 'visibility'"
              @click:append="passwordVisible = !passwordVisible"
              :type="passwordVisible ? 'text' : 'password'"
              :error-messages="errors.password"
          />
          <v-tooltip
              top
              color="orange"
              max-width="350"
              content-class="form-tooltip"
          >
            <template v-slot:activator="{ on }">
            <v-icon v-on="on" class="ml-1 mb-1">info</v-icon>
              </template>
            <ul>
              <li>Password must be at least 8 characters long.</li>
              <li>Password must contain at least 3 character categories among the following:
                <ul>
                  <li>Lowercase characters (a-z)</li>
                  <li>Uppercase characters (A-Z)</li>
                  <li>Digits (0-9)</li>
                  <li>Special characters</li>
                </ul>
              </li>
            </ul>
          </v-tooltip>
        </v-layout>
      <v-text-field
        placeholder="Confirm password"
        name="confirm"
        color="orange"
        v-model="confirm"
        :type="passwordVisible ? 'text' : 'password'"
        :error-messages="errors.confirm"
      />
      <slot />
      <v-btn
        color="orange"
        :disabled="invalidInput"
        class="mx-0 white--text"
        id="sign-up-btn"
        @click="signUp"
      >
        Sign Up
      </v-btn>
      <p class="cookies">
        This website uses cookies. By continuing to use this website you consent to their use.
      </p>
    </v-form>
  </v-card-text>
</template>

<script>
import FormMixin from '@/mixins/Form'
import { waitCursor } from '@/util'
import { postRetryCond } from '@/http'

export default {
  mixins: [FormMixin],
  props: {
    isValid: {
      type: Boolean,
      default: null
    }
  },
  data () {
    return {
      username: '',
      email: '',
      password: '',
      confirm: '',
      passwordVisible: false
    }
  },
  computed: {
    app () {
      return this.$store.state.app
    },
    invalidInput () {
      return (this.isValid === null) ? this.validateInput(this.$data) : !this.isValid
    }
  },
  methods: {
    validateInput (data) {
      return ['username', 'email', 'password', 'confirm'].some(k => data[k] === '')
    },
    signUp () {
      this.clearErrors()
      waitCursor(true)
      const data = {
        username: this.username.trim(),
        email: this.email.trim(),
        password: this.password,
        confirm: this.confirm
      }
      this.$http.post('/auth/signup', data, { 'axios-retry': { retries: 5, retryCondition: error => postRetryCond(error) } })
        .then((resp) => {
          this.$notification.show('Confirmation email was sent to your email address')
          this.$store.dispatch('clearUserData')
          this.$store.commit('user', resp.data)
          this.$emit('success')
          waitCursor(false)
        })
        .catch(err => {
          this.handleError(err, 'Failed to send confirmation email')
          waitCursor(false)
        })
    }
  }
}
</script>

<style lang="scss" scoped>

.v-tooltip {
  cursor: default;
}
.cookies {
  text-align: center;
  color: #777;
  margin-top: 1em;
  font-size: 0.875em;
}
</style>

<style lang="scss">
.form-tooltip {
  opacity: 0.95!important;
  ul {
    padding-left: 1em;
  }
}
</style>
