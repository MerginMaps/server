<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <app-onboarding-page>
    <template #header>
      <h1 class="text-6xl">Email confirmation</h1>
    </template>

    <template v-if="verified"
      ><img src="@/assets/neutral.svg" alt="MerginMaps neutral" />Your email
      address has been verified.</template
    >
    <template v-else
      ><img src="@/assets/negative.svg" alt="MerginMaps negative" />Invalid
      token</template
    >
    <PButton data-cy="verify-email-btn" @click="$router.push({ name: 'home' })"
      >Continue
    </PButton>
  </app-onboarding-page>
</template>

<script lang="ts">
import { defineComponent } from 'vue'

import AppOnboardingPage from '@/common/components/AppOnboardingPage.vue'
import { UserApi } from '@/modules/user/userApi'

export default defineComponent({
  name: 'VerifyEmailView',
  data() {
    return {
      verified: false
    }
  },
  computed: {
    token() {
      return this.$route.params.token as string
    }
  },
  async created() {
    try {
      await UserApi.confirmEmail(this.token)
      this.verified = true
    } catch (e) {
      this.verified = false
    }
  },
  components: { AppOnboardingPage }
})
</script>

<style scoped lang="scss"></style>
