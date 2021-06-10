# Copyright (C) 2018 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

<template>
  <v-card v-on:keyup.enter="submit">
    <v-card-title>
      <span class="headline">Edit profile</span>
    </v-card-title>
    <v-card-text>
      <p
        v-if="errorMsg"
        class="text-xs-center red--text"
        v-text="errorMsg"
      />
      <v-form class="layout column">
        <v-text-field
          label="First name"
          v-model="editedProfile.first_name"
          :error-messages="errors.first_name"
          @keyup.enter="submit"
        />
        <v-text-field
          label="Last name"
          v-model="editedProfile.last_name"
          :error-messages="errors.last_name"
          @keyup.enter="submit"
        />
        <v-text-field
          label="Email address"
          v-model="editedProfile.email"
          :error-messages="errors.email"
          @keyup.enter="submit"
        />
        <v-checkbox
          label="Receive notifications"
          color="orange"
          v-model="editedProfile.receive_notifications"
          :error-messages="errors.receive_notifications"
        />

        <v-card-actions>
          <v-spacer/>
          <v-btn
              class="text--primary"
              @click="$dialog.close"
          >
            Close
          </v-btn>
          <v-btn
            class="primary white--text"
            @click="submit"
          >
            Save
          </v-btn>
        </v-card-actions>
      </v-form>
    </v-card-text>
  </v-card>
</template>

<script>
import FormMixin from '@/mixins/Form'
import { waitCursor } from '../../util'
import { postRetryCond } from '../../http'

export default {
  props: {
    profile: Object
  },
  mixins: [FormMixin],
  data () {
    return {
      editedProfile: Object.assign({}, this.profile)
    }
  },
  methods: {
    submit () {
      this.clearErrors()
      const keys = ['first_name', 'last_name', 'email']
      keys.forEach(key => { this.editedProfile[key] = this.editedProfile[key].trim() })
      waitCursor(true)
      this.$http.post('/auth/user/profile', this.editedProfile, { 'axios-retry': { retries: 5, retryCondition: error => postRetryCond(error) } })
        .then(() => {
          this.$dialog.close()
          waitCursor(false)
          this.$emit('success')
          this.$notification.show('Profile has been changed')
        })
        .catch(err => {
          this.handleError(err, 'Failed to change profile')
          waitCursor(false)
        })
    }
  }
}
</script>
