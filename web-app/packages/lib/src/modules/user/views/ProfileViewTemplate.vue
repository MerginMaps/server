<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <article class="profile-view">
    <app-container
      ><section
        class="flex flex-column lg:flex-row lg:align-items-center row-gap-3"
      >
        <!-- Title with buttons -->
        <h1 class="headline-h3 text-color font-semibold">
          {{ t('AccountDetails') }}
        </h1>
        <div
          v-if="loggedUser?.can_edit_profile"
          class="flex flex-grow-1 align-items-center lg:justify-content-end"
        >
          <PButton
            @click="editProfileDialog"
            icon="ti ti-pencil"
            :label="t('EditAccount')"
            class="w-auto mr-1"
            data-cy="profile-edit-btn"
          />
          <PButton
            @click="changePasswordDialog"
            severity="secondary"
            data-cy="profile-change-password-btn"
            class="w-auto"
            icon="ti ti-lock"
            :label="t('ChangePassword')"
          />
        </div></section
    ></app-container>
    <app-container v-if="$slots.additionalBeforeContent"
      ><slot name="additionalBeforeContent"></slot
    ></app-container>
    <app-container v-if="!loggedUser?.verified_email">
      <app-section-banner>
        <template #header-image
          ><img width="50" height="50" src="@/assets/warning.svg"
        /></template>
        <template #title>{{ t('PleaseVerifyYourEmail') }}</template>
        <template #description>{{
          t('WeSentYouAVerificationEmailToTheAccountYouProvidedDuringSignup')
        }}</template>
        <template #header-actions
          ><PButton
            @click="resendConfirmationEmail"
            severity="secondary"
            data-cy="profile-send-email-btn"
            :label="t('SendConfirmationEmail')"
        /></template>
      </app-section-banner>
    </app-container>
    <app-container>
      <app-section class="p-4">
        <div class="flex flex-column align-items-center row-gap-3 text-center">
          <PAvatar
            :label="$filters.getAvatar(loggedUser.email, loggedUser.name)"
            shape="circle"
            size="xlarge"
            :pt="{
              root: {
                class: 'font-semibold text-color-forest'
              }
            }"
          />
          <h3 class="headline-h2" data-cy="profile-username">
            {{ loggedUser?.username }}
          </h3>
          <p
            class="m-0 paragraph-p6 overflow-wrap-anywhere"
            data-cy="profile-email"
          >
            <i
              v-if="!loggedUser?.verified_email"
              v-tooltip.top="{
                value: t('EmailVerificationStatus')
              }"
              class="ti ti-alert-circle-filled"
              data-cy="project-form-missing-project"
              style="color: var(--grape-color)"
            ></i
            >&nbsp;{{ loggedUser?.email }}
          </p>
          <dl class="profile-view-detail-list grid grid-nogutter paragraph-p5">
            <div
              class="col-6 flex flex-column align-items-start text-left flex-wrap"
            >
              <dt class="paragraph-p6 opacity-80 mb-2">
                {{ t('FullName') }}
              </dt>
              <dd class="font-semibold" data-cy="profile-name">
                {{ loggedUser?.name || '-' }}
              </dd>
            </div>
            <div class="col-6 flex flex-column align-items-end">
              <dt class="paragraph-p6 opacity-80 mb-2">
                {{ t('Registered') }}
              </dt>
              <dd class="font-semibold" data-cy="profile-registered">
                {{ $filters.date(loggedUser?.registration_date) }}
              </dd>
            </div>
          </dl>
        </div>
      </app-section>
    </app-container>
    <app-container>
      <app-section>
        <template #title>{{ t('Advanced') }}</template>
        <div class="flex flex-column row-gap-3 paragraph-p5 px-4 pb-4">
          <div
            v-if="loggedUser?.can_edit_profile"
            :class="[
              'flex flex-column align-items-start',
              'row-gap-2',
              'md:align-items-center md:flex-row'
            ]"
          >
            <div class="flex-grow-1">
              <p class="title-t3">{{ t('ReceiveNotifications') }}</p>
              <span class="paragraph-p6 opacity-80">{{
                t('WeWillSendYouInformationAboutWorkspaceActivity')
              }}</span>
            </div>
            <div
              class="flex align-items-center flex-shrink-0"
              data-cy="profile-notification"
            >
              <PInputSwitch
                :modelValue="loggedUser?.receive_notifications"
                @change="receiveNotificationsChange"
              />
            </div>
          </div>
          <div
            :class="[
              'flex flex-column align-items-start',
              'row-gap-2',
              'md:align-items-center md:flex-row'
            ]"
          >
            <div class="flex-grow-1">
              <p class="title-t3">{{ t('CloseAccount') }}</p>
              <span class="paragraph-p6 opacity-80">{{
                t(
                  'YourAccountWillBeClosedInCaseYouAreAnOwnerOfAWorkspaceYouMightNeedToTransferTheOwnershipFirstOrCloseTheWorkspace'
                )
              }}</span>
            </div>
            <div class="flex-shrink-0">
              <PButton
                @click="confirmDeleteUser"
                severity="danger"
                data-cy="profile-close-account-btn"
                :label="t('CloseAccount')"
              />
            </div>
          </div>
        </div>
      </app-section>
    </app-container>
    <app-container><slot name="additionalContent"></slot></app-container>
  </article>
</template>

<script lang="ts">
import { mapState, mapActions } from 'pinia'
import { defineComponent } from 'vue'

import DeleteAccountDialog from '../components/DeleteAccountConfirm.vue'

import returnTranslation from '@/../../lang/translate'
import AppContainer from '@/common/components/AppContainer.vue'
import AppSection from '@/common/components/AppSection.vue'
import AppSectionBanner from '@/common/components/AppSectionBanner.vue'
import { DeleteAccountConfirmProps, useDialogStore } from '@/modules'
import { useLayoutStore } from '@/modules/layout/store'
import ChangePasswordForm from '@/modules/user/components/ChangePasswordForm.vue'
import EditProfileForm from '@/modules/user/components/EditProfileForm.vue'
import { useUserStore } from '@/modules/user/store'

const t = (key: string) => returnTranslation(import.meta.env.VITE_LANG, key)

export default defineComponent({
  name: 'ProfileViewTemplate',
  setup() {
    return { t }
  },
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
        username: this.loggedUser?.username
      }
      const listeners = {
        confirm: async () => await this.closeUserProfile()
      }
      this.show({
        component: DeleteAccountDialog,
        params: {
          props,
          listeners,
          dialog: { header: t('CloseAccount') }
        }
      })
    },
    changePasswordDialog() {
      const dialog = { persistent: true, header: t('ChangePassword') }
      this.show({
        component: ChangePasswordForm,
        params: {
          dialog
        }
      })
    },
    editProfileDialog() {
      const props = { profile: this.loggedUser }
      const dialog = { header: t('EditAccount') }
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
          receive_notifications: !this.loggedUser?.receive_notifications
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
