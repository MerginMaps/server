<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <app-onboarding-page>
    <template #header>
      <h1 class="headline-h1">
        {{
          unlocked ? 'Unlock your account' : 'Unlock link is invalid or expired'
        }}
      </h1>
    </template>
    <div class="flex flex-column gap-4 align-items-center">
      <template v-if="unlocked">
        <img src="@/assets/neutral.svg" alt="MerginMaps neutral" /><span
          class="opacity-80 paragraph-p5"
          >Your account has been unlocked. You can now sign in.</span
        >
        <PButton
          data-cy="unlock-account-btn"
          @click="router.push({ name: 'login' })"
          class="w-full"
          label="Continue"
        />
      </template>
      <template v-else>
        <img src="@/assets/negative.svg" alt="MerginMaps negative" />
      </template>
    </div>
  </app-onboarding-page>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import AppOnboardingPage from '@/common/components/AppOnboardingPage.vue'
import { UserApi } from '@/modules/user/userApi'

const route = useRoute()
const router = useRouter()

const unlocked = ref(false)

onMounted(async () => {
  try {
    await UserApi.unlockAccount(route.params.token as string)
    unlocked.value = true
  } catch {
    unlocked.value = false
  }
})
</script>

<style scoped lang="scss"></style>
