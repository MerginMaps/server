<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <div class="flex flex-column pb-4">
    <span class="p-input-filled">
      <label for="oldPassowrd">{{ t('OldPassword') }}</label>
      <PPassword
        id="oldPassowrd"
        v-model="oldPassword"
        data-cy="user-change-password-old"
        :class="[errors.old_password ? 'p-invalid' : '']"
        toggleMask
        :feedback="false"
        :prompt-label="t('EnterPassword')"
        aria-describedby="old-password-error"
        :placeholder="t('MustBeAtLeastCharacters')"
      />
      <span class="p-error paragraph-p6" id="old-password-error">{{
        errors.old_password?.[0] || '&nbsp;'
      }}</span>
    </span>

    <span class="p-input-filled">
      <app-password-tooltip for="newPassword"
        ><template #label>{{ t('NewPassword') }}</template>
      </app-password-tooltip>

      <PPassword
        id="newPassword"
        v-model="password"
        :class="[errors.password ? 'p-invalid' : '']"
        data-cy="user-change-password-new"
        aria-describedby="password-error"
        toggleMask
        :feedback="false"
        :prompt-label="t('EnterPassword')"
        :placeholder="t('MustBeAtLeastCharacters')"
      />
      <span class="p-error paragraph-p6" id="password-error">{{
        errors.password?.[0]
          ? errors.password?.[0].startsWith('Password')
            ? t(
                'PasswordMustBeAtLeastCharactersLongAndIncludeAtLeastThreeOfTheFollowingLowercaseLettersUppercaseLettersNumbersOrSpecialCharacters'
              )
            : errors.password[0]
          : '&nbsp;'
      }}</span>
    </span>

    <span class="p-input-filled">
      <app-password-tooltip for="confirm">
        <template #label>{{ t('ConfirmPassword') }}</template>
      </app-password-tooltip>

      <PPassword
        id="confirm"
        v-model="confirm"
        :class="[errors.confirm ? 'p-invalid' : '']"
        data-cy="user-change-password-confirm"
        aria-describedby="confirm-password-error"
        toggleMask
        :feedback="false"
        :prompt-label="t('EnterPassword')"
        :placeholder="t('MustBeAtLeastCharacters')"
      />

      <span class="p-error paragraph-p6" id="confirm-password-error">{{
        errors.confirm?.[0] || '&nbsp;'
      }}</span>
    </span>

    <!-- Footer -->
    <div
      class="w-full flex flex-column lg:flex-row justify-content-between align-items-center mt-4"
    >
      <PButton
        severity="secondary"
        @click="close"
        class="flex w-12 mb-2 lg:mb-0 lg:mr-2 lg:w-6 justify-content-center"
        data-cy="user-change-password-close-btn"
        >{{ t('Cancel') }}</PButton
      >

      <PButton
        :disabled="!password || !oldPassword || !confirm"
        @click="changePassword"
        class="flex w-12 lg:w-6 justify-content-center"
        data-cy="user-change-password-change-btn"
      >
        {{ t('SaveChanges') }}
      </PButton>
    </div>
  </div>
</template>

<script lang="ts">
import { mapActions, mapState } from 'pinia'
import { defineComponent } from 'vue'

import returnTranslation from '@/../../lang/translate'
import AppPasswordTooltip from '@/common/components/AppPasswordTooltip.vue'
import { waitCursor } from '@/common/html_utils'
import { useDialogStore } from '@/modules/dialog/store'
import { useFormStore } from '@/modules/form/store'
import { useUserStore } from '@/modules/user/store'

const t = (key: string) => returnTranslation(import.meta.env.VITE_LANG, key)

export default defineComponent({
  setup() {
    return { t }
  },
  data() {
    return {
      oldPassword: '',
      password: '',
      confirm: '',
      passwordVisible: false
    }
  },
  computed: {
    ...mapState(useFormStore, ['getErrorByComponentId']),
    errors() {
      return this.getErrorByComponentId(this.merginComponentUuid) ?? {}
    }
  },
  beforeUnmount() {
    this.clearErrors({
      componentId: this.merginComponentUuid,
      keepNotification: true
    })
  },
  methods: {
    ...mapActions(useFormStore, ['clearErrors']),
    ...mapActions(useDialogStore, ['close']),
    ...mapActions(useUserStore, {
      changePasswordAction: 'changePassword'
    }),
    changePassword() {
      this.clearErrors({ componentId: this.merginComponentUuid })
      const data = {
        old_password: this.oldPassword,
        password: this.password,
        confirm: this.confirm
      }
      waitCursor(true)
      this.changePasswordAction({ data, componentId: this.merginComponentUuid })
    }
  },
  components: { AppPasswordTooltip }
})
</script>
