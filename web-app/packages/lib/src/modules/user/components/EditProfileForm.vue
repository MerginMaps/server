<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <form @submit.prevent="submit" class="flex flex-column pb-4 row-gap-1">
    <span class="p-input-filled">
      <label class="text-xs" for="first-name">First name</label>
      <PInputText
        id="first-name"
        v-model="editedProfile.first_name"
        data-cy="profile-edit-first-name"
        :class="['w-full my-1', errors.first_name ? 'p-invalid' : '']"
        toggleMask
        :feedback="false"
        aria-describedby="first-name-error"
      />
      <span class="p-error text-xs" id="first-name-error">{{
        errors.first_name?.[0] || '&nbsp;'
      }}</span>
    </span>

    <span class="p-input-filled">
      <label class="text-xs" for="last-name">Last name</label>
      <PInputText
        id="last-name"
        v-model="editedProfile.last_name"
        data-cy="profile-edit-last-name"
        :class="['w-full my-1', errors.last_name ? 'p-invalid' : '']"
        toggleMask
        :feedback="false"
        aria-describedby="last-name-error"
      />
      <span class="p-error text-xs" id="last-name-error">{{
        errors.last_name?.[0] || '&nbsp;'
      }}</span>
    </span>

    <span class="p-input-filled">
      <label class="text-xs" for="email">Email</label>
      <PInputText
        id="email"
        v-model="editedProfile.email"
        data-cy="profile-edit-email"
        :class="['w-full my-1', errors.email ? 'p-invalid' : '']"
        toggleMask
        :feedback="false"
        aria-describedby="email-error"
      />
      <span class="p-error text-xs" id="email-error">{{
        errors.email?.[0] || '&nbsp;'
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
        data-cy="profile-edit-close-btn"
        >Cancel</PButton
      >

      <PButton
        type="submit"
        class="flex w-12 lg:w-6 justify-content-center"
        data-cy="profile-edit-save-btn"
      >
        Save changes
      </PButton>
    </div>
  </form>
</template>

<script lang="ts">
import { mapActions, mapState } from 'pinia'
import { PropType, defineComponent } from 'vue'

import { EditUserProfileParams } from '../types'

import { useDialogStore } from '@/modules/dialog/store'
import { useFormStore } from '@/modules/form/store'
import { useUserStore } from '@/modules/user/store'

export default defineComponent({
  props: {
    profile: Object as PropType<EditUserProfileParams>
  },
  data() {
    return {
      editedProfile: Object.assign({}, this.profile)
    }
  },
  computed: {
    ...mapState(useFormStore, ['getErrorByComponentId']),
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
    ...mapActions(useFormStore, ['clearErrors']),
    ...mapActions(useUserStore, ['editUserProfile']),
    ...mapActions(useDialogStore, ['close']),

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
