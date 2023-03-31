<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <v-card v-on:keyup.enter="submit" cy-data="profile-edit-form">
    <v-card-title>
      <span class="text-h5">Edit profile</span>
    </v-card-title>
    <v-card-text>
      <v-form @submit.prevent class="layout column">
        <v-text-field
          label="First name"
          v-model="editedProfile.first_name"
          cy-data="profile-edit-first-name"
          :error-messages="errors.first_name"
          @keyup.enter="submit"
        />
        <v-text-field
          label="Last name"
          v-model="editedProfile.last_name"
          cy-data="profile-edit-last-name"
          :error-messages="errors.last_name"
          @keyup.enter="submit"
        />
        <v-text-field
          label="Email address"
          v-model="editedProfile.email"
          cy-data="profile-edit-email"
          :error-messages="errors.email"
          @keyup.enter="submit"
        />
        <v-checkbox
          label="Receive notifications"
          color="orange"
          cy-data="profile-edit-notification"
          v-model="editedProfile.receive_notifications"
          :error-messages="errors.receive_notifications"
        />

        <v-card-actions>
          <v-spacer />
          <v-btn
            class="text--primary"
            @click="close"
            cy-data="profile-edit-close-btn"
          >
            Close
          </v-btn>
          <v-btn
            class="primary white--text"
            cy-data="profile-edit-save-btn"
            @click="submit"
          >
            Save
          </v-btn>
        </v-card-actions>
      </v-form>
    </v-card-text>
  </v-card>
</template>

<script lang="ts">
import Vue from 'vue'
import { mapActions, mapGetters } from 'vuex'

export default Vue.extend({
  props: {
    profile: Object
  },
  data() {
    return {
      editedProfile: Object.assign({}, this.profile)
    }
  },
  computed: {
    ...mapGetters('formModule', ['getErrorByComponentId']),
    errors() {
      return this.getErrorByComponentId(this.merginComponentUuid) ?? {}
    }
  },
  beforeDestroy() {
    this.clearErrors({
      componentId: this.merginComponentUuid,
      keepNotification: true
    })
  },
  methods: {
    ...mapActions('formModule', ['clearErrors']),
    ...mapActions('userModule', ['editUserProfile']),
    ...mapActions('dialogModule', ['close']),

    submit() {
      this.clearErrors({ componentId: this.merginComponentUuid })
      const keys = ['first_name', 'last_name', 'email']
      keys.forEach((key) => {
        if (this.editedProfile[key])
          this.editedProfile[key] = this.editedProfile[key].trim()
      })
      this.editUserProfile({
        editedUser: this.editedProfile,
        componentId: this.merginComponentUuid
      })
    }
  }
})
</script>
