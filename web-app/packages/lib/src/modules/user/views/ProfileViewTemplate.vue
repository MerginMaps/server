<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <div class="profile-view">
    <app-container
      ><section
        class="flex flex-column lg:flex-row lg:align-items-center row-gap-3"
      >
        <!-- Title with buttons -->
        <h1 class="text-2xl text-color font-semibold">Account details</h1>
        <div class="flex flex-grow-1 align-items-center lg:justify-content-end">
          <PButton
            @click="editProfileDialog"
            data-cy="action-button-create"
            icon="ti ti-pencil"
            label="Edit account"
            class="w-auto mr-1"
            cy-data="profile-edit-btn"
          />
          <PButton
            @click="changePasswordDialog"
            severity="secondary"
            cy-data="profile-change-password-btn"
            class="w-auto"
            icon="ti ti-lock"
            label="Change password"
          />
        </div></section
    ></app-container>
    <app-container v-if="$slots.additionalBeforeContent"
      ><slot name="additionalBeforeContent"></slot
    ></app-container>
    <app-container v-if="!loggedUser.verified_email">
      <app-section-banner>
        <template #header-image
          ><img width="50" height="50" src="@/assets/warning.svg"
        /></template>
        <template #title>Please verify your email</template>
        <template #description
          >We sent you a verification email to the account you provided during
          signup.</template
        >
        <template #header-actions
          ><PButton @click="resendConfirmationEmail" severity="secondary"
            >Send confirmation email
          </PButton></template
        >
      </app-section-banner>
    </app-container>
    <app-container>
      <app-section class="p-4">
        <div class="flex flex-column align-items-center row-gap-3 text-center">
          <PAvatar
            :label="(loggedUser.username ?? '').charAt(0).toUpperCase()"
            shape="circle"
            size="xlarge"
            :pt="{
              root: {
                class:
                  'text-5xl surface-ground font-semibold text-color-forest',
                style: {
                  width: '120px',
                  height: '120px'
                }
              }
            }"
          />
          <h3 class="text-4xl" cy-data="profile-username">
            {{ loggedUser.username }}
          </h3>
          <p class="m-0 text-xs" cy-data="profile-email">
            <i
              v-if="!loggedUser.verified_email"
              v-tooltip.top="{
                value: 'Email verification status'
              }"
              class="ti ti-alert-circle-filled"
              data-cy="project-form-missing-project"
              style="color: var(--grape-color)"
            ></i
            >&nbsp;{{ loggedUser.email }}
          </p>
          <dl class="profile-view-detail-list grid grid-nogutter text-sm">
            <div
              class="col-6 flex flex-column align-items-start text-left flex-wrap"
            >
              <dt class="text-xs opacity-80 mb-2">Full name</dt>
              <dl class="font-semibold" cy-data="profile-name">
                {{ loggedUser.name || '-' }}
              </dl>
            </div>
            <div class="col-6 flex flex-column align-items-end">
              <dt class="text-xs opacity-80 mb-2">Registered</dt>
              <dl class="font-semibold" cy-data="profile-registered">
                {{ $filters.date(loggedUser.registration_date) }}
              </dl>
            </div>
          </dl>
        </div>
      </app-section>
    </app-container>
    <app-container>
      <app-section-banner>
        <template #title>Advanced</template>
        <div class="flex align-items-center text-sm py-2">
          <div class="flex-grow-1">
            <p class="font-semibold my-2">Receive notifications</p>
            <span class="text-xs opacity-80"
              >We will send you information about workspace activity and a
              monthly bulletin email</span
            >
          </div>
          <div
            class="flex align-items-center flex-shrink-0"
            cy-data="profile-notification"
          >
            <PInputSwitch
              :modelValue="loggedUser.receive_notifications"
              @change="receiveNotificationsChange"
            />
          </div>
        </div>
        <div class="flex align-items-center text-sm py-2">
          <div class="flex-grow-1">
            <p class="font-semibold my-2">Close account</p>
            <span class="text-xs opacity-80"
              >Your account will be closed. In case you are an owner of a
              workspace, you might need to transfer the ownership first or close
              the workspace.</span
            >
          </div>
          <div class="flex-shrink-0">
            <PButton
              @click="confirmDeleteUser"
              severity="danger"
              cy-data="profile-close-account-btn"
            >
              Close account</PButton
            >
          </div>
        </div>
      </app-section-banner>
    </app-container>
    <app-container><slot name="additionalContent"></slot></app-container>
  </div>
</template>

<script lang="ts">
import { mapState, mapActions } from 'pinia'
import { defineComponent } from 'vue'

import DeleteAccountDialog from '../components/DeleteAccountConfirm.vue'

import AppContainer from '@/common/components/AppContainer.vue'
import AppSection from '@/common/components/AppSection.vue'
import AppSectionBanner from '@/common/components/AppSectionBanner.vue'
import { DeleteAccountConfirmProps, useDialogStore } from '@/modules'
import { useLayoutStore } from '@/modules/layout/store'
import ChangePasswordForm from '@/modules/user/components/ChangePasswordForm.vue'
import EditProfileForm from '@/modules/user/components/EditProfileForm.vue'
import { useUserStore } from '@/modules/user/store'

export default defineComponent({
  name: 'ProfileViewTemplate',
  props: {
    name: String
  },
  components: { AppContainer, AppSection, AppSectionBanner },
  data() {
    return {
      dialog: false
    }
  },
  computed: {
    ...mapState(useLayoutStore, ['drawer']),
    ...mapState(useUserStore, ['loggedUser'])
  },
  created() {
    this.fetchUserProfile()
  },
  watch: {
    name: function () {
      this.fetchUserProfile()
    }
  },
  methods: {
    ...mapActions(useDialogStore, ['show']),
    ...mapActions(useUserStore, {
      fetchUserProfile: 'fetchUserProfile',
      resendConfirmationEmailToUser: 'resendConfirmationEmail',
      closeUserProfile: 'closeUserProfile',
      editUserProfile: 'editUserProfile'
    }),

    resendConfirmationEmail() {
      this.resendConfirmationEmailToUser({ email: this.loggedUser?.email })
    },
    confirmDeleteUser() {
      const props: DeleteAccountConfirmProps = {
        username: this.loggedUser.username
      }
      const listeners = {
        confirm: async () => await this.closeUserProfile()
      }
      this.show({
        component: DeleteAccountDialog,
        params: {
          props,
          listeners,
          dialog: { header: 'Close account' }
        }
      })
    },
    changePasswordDialog() {
      const dialog = { persistent: true, header: 'Change password' }
      this.show({
        component: ChangePasswordForm,
        params: {
          dialog
        }
      })
    },
    editProfileDialog() {
      const props = { profile: this.loggedUser }
      const dialog = { header: 'Edit account' }
      this.show({
        component: EditProfileForm,
        params: {
          props,
          dialog
        }
      })
    },
    receiveNotificationsChange() {
      this.editUserProfile({
        editedUser: {
          ...this.loggedUser,
          receive_notifications: !this.loggedUser.receive_notifications
        },
        componentId: this.merginComponentUuid
      })
    }
  }
})
</script>

<style lang="scss" scoped>
.profile-view {
  &-detail-list {
    max-width: 640px;
    width: 100%;
  }
}
</style>
