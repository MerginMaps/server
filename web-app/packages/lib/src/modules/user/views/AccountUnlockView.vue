<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <app-onboarding-page>
    <template #header>
      <h1 class="headline-h1">Account unlock</h1>
    </template>
    <div class="flex flex-column gap-4 align-items-center">
      <template v-if="unlocked"
        ><img src="@/assets/neutral.svg" alt="MerginMaps neutral" /><span
          class="opacity-80 paragraph-p5"
          >Your account has been unlocked. You can now sign in.</span
        ></template
      >
      <template v-else
        ><img src="@/assets/negative.svg" alt="MerginMaps negative" /><span
          class="opacity-80 paragraph-p5"
          >This unlock link is invalid or has expired.</span
        ></template
      >
      <PButton
        data-cy="unlock-account-btn"
        @click="$router.push({ name: 'login' })"
        class="w-full"
        label="Continue"
      />
    </div>
  </app-onboarding-page>
</template>

<script lang="ts">
import { defineComponent } from 'vue'

import AppOnboardingPage from '@/common/components/AppOnboardingPage.vue'
import { UserApi } from '@/modules/user/userApi'

export default defineComponent({
  name: 'AccountUnlockView',
  data() {
    return {
      unlocked: false
    }
  },
  computed: {
    token() {
      return this.$route.params.token as string
    }
  },
  async created() {
    try {
      await UserApi.unlockAccount(this.token)
      this.unlocked = true
    } catch (e) {
      this.unlocked = false
    }
  },
  components: { AppOnboardingPage }
})
</script>

<style scoped lang="scss"></style>
