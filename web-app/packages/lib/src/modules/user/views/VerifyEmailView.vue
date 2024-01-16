<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <section
    class="relative verify-email-view flex align-items-center justify-content-center h-full"
  >
    <aside class="absolute top-0 left-0 m-4">
      <img src="@/assets/mm-logo.svg" alt="Mergin Maps logo" />
    </aside>
    <div
      class="verify-email-view-container flex flex-column align-items-center text-center row-gap-4 p-4 lg:p-0"
    >
      <header>
        <h1 class="text-6xl">Email confirmation</h1>
      </header>

      <template v-if="verified"
        ><img src="@/assets/neutral.svg" alt="MerginMaps neutral" />Your email
        address has been verified.</template
      >
      <template v-else
        ><img src="@/assets/negative.svg" alt="MerginMaps negative" />Invalid
        token</template
      >
      <PButton
        data-cy="verify-email-btn"
        @click="$router.push({ name: 'home' })"
        >Continue
      </PButton>
    </div>
  </section>
</template>

<script lang="ts">
import { defineComponent } from 'vue'

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
  }
})
</script>

<style scoped lang="scss">
.verify-email-view {
  &-container {
    max-width: 480px;
    width: 100%;
  }
}
</style>
