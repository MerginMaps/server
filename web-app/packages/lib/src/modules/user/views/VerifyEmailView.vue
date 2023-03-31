<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <custom-page>
    <v-card style="min-width: 300px" class="text-center">
      <v-card-title class="justify-center primary--text font-weight-bold ml-3">
        <h3>Email confirmation</h3>
      </v-card-title>
      <v-card-text>
        <p v-if="verified">Your email address has been verified.</p>
        <p v-else class="error--text">Invalid token</p>
        <br />
        <v-btn
          data-cy="verify-email-btn"
          class="align-self-center orange white--text"
          href="/"
          >Continue
        </v-btn>
      </v-card-text>
    </v-card>
  </custom-page>
</template>

<script>
import CustomPage from '@/common/components/CustomPage'
import { UserApi } from '@/modules/user/userApi'

// TODO: deprecated?
export default {
  name: 'VerifyEmailView',
  components: { CustomPage },
  data() {
    return {
      verified: false
    }
  },
  computed: {
    token() {
      return this.$route.params.token
    }
  },
  async created() {
    try {
      await UserApi.confirmEmail(this.token)
      this.verified = true
    } catch (e) {
      this.verified = false
    }
  }
}
</script>

<style scoped></style>
