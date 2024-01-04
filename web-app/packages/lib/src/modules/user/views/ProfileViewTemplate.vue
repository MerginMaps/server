<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <div class="profile-view">
    <app-container
      ><section class="flex flex-column lg:flex-row lg:align-items-center">
        <!-- Title with buttons -->
        <h1 class="text-2xl text-color font-semibold mb-3 lg:mb-0">
          Account details
        </h1>
        <div
          class="flex flex-grow-1 align-items-center lg:justify-content-end mb-3 lg:mb-0"
        >
          <PButton
            @click="editProfileDialog"
            data-cy="action-button-create"
            icon="ti ti-pencil"
            label="Edit profile"
            class="w-auto mr-1"
            cy-data="profile-edit-btn"
          />
          <PButton
            @click="changePasswordDialog"
            severity="secondary"
            outlined
            cy-data="profile-change-password-btn"
            class="w-auto"
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
          ><PButton
            @click="resendConfirmationEmail"
            severity="secondary"
            outlined
            >Send confirmation email
          </PButton></template
        >
      </app-section-banner>
    </app-container>
    <app-container>
      <app-section class="p-4">
        <div
          v-if="loggedUser"
          class="flex flex-column align-items-center row-gap-3 text-center"
        >
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
            <p class="font-semibold py-1 m-0">Receive notifications</p>
            <span class="text-xs opacity-80"
              >We will send you information about workspace activity and a
              monthly bulletin email</span
            >
          </div>
          <div class="flex-shrink-0" cy-data="profile-notification">
            <PInputSwitch
              :modelValue="loggedUser.receive_notifications"
              @change="receiveNotificationsChange"
            />
          </div>
        </div>
        <div class="flex align-items-center text-sm py-2">
          <div class="flex-grow-1">
            <p class="font-semibold m-0 py-1">Close account</p>
            <span class="text-xs opacity-80">All data will be lost</span>
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

  <page-view
    :style="`padding-left: ${
      drawer ? 260 : 20
    }px; overflow-y: auto; padding-right:20px; margin-right: 0px;`"
  >
    <v-layout class="column main-content fill-height">
      <v-container>
        <slot name="additionalBeforeContent"></slot>
        <v-row>
          <v-col cols="12" class="pa-0">
            <v-card
              v-if="!loggedUser.verified_email"
              variant="outlined"
              class="mt-3"
              style="
                background-color: #ffc863;
                color: rgba(0, 0, 0, 0.87);
                overflow: hidden;
              "
            >
              <v-card-text
                >Your email hasn't been confirmed yet
                <v-btn
                  color="#ecf3ff"
                  @click="resendConfirmationEmail"
                  style="float: right"
                  >Send confirmation email
                </v-btn></v-card-text
              >
            </v-card>
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12" class="pa-0">
            <v-card variant="flat">
              <v-card-text>
                <div class="profile">
                  <h1 class="text-primary">Profile</h1>
                  <br />
                  <v-divider />
                  <v-layout align-center>
                    <v-row>
                      <v-col>
                        <!-- Render profile -->
                        <div class="section" cy-data="profile-info">
                          <ul v-if="loggedUser">
                            <li cy-data="profile-username">
                              <b> Username: </b>{{ loggedUser.username }}
                            </li>
                            <li cy-data="profile-name">
                              <b> Name: </b>{{ loggedUser.name }}
                            </li>
                            <li cy-data="profile-email">
                              <b> Email: </b>{{ loggedUser.email }}
                              <v-tooltip
                                location="top"
                                v-if="
                                  'project-versions' !== $route.name &&
                                  'project-versions-detail' !== $route.name
                                "
                              >
                                <template v-slot:activator="{ props }">
                                  <span v-bind="props">
                                    <v-icon
                                      v-if="loggedUser.verified_email"
                                      color="green"
                                      >check</v-icon
                                    >
                                    <v-icon v-else color="red">clear</v-icon>
                                  </span>
                                </template>
                                <span>Email verification status</span>
                              </v-tooltip>
                            </li>
                            <li cy-data="profile-notification">
                              <b> Receive notifications: </b>
                              <v-icon
                                v-if="loggedUser.receive_notifications"
                                color="green"
                                >check</v-icon
                              >
                              <v-icon v-else color="red">clear</v-icon>
                            </li>
                            <li cy-data="profile-registered">
                              <b> Registered: </b
                              >{{ $filters.date(loggedUser.registration_date) }}
                            </li>
                          </ul>
                          <br />
                        </div>
                        <v-spacer />
                      </v-col>
                      <!-- actions -->
                      <v-col>
                        <div>
                          <div>
                            <v-btn
                              @click="changePasswordDialog"
                              class="text-primary"
                              cy-data="profile-change-password-btn"
                            >
                              <v-icon class="mr-2">edit</v-icon>
                              Change password
                            </v-btn>
                          </div>
                          <div>
                            <v-btn
                              @click="editProfileDialog"
                              class="text-primary"
                              cy-data="profile-edit-btn"
                            >
                              <v-icon class="mr-2">edit</v-icon>
                              Edit profile
                            </v-btn>
                          </div>
                          <div>
                            <v-btn
                              @click="showConfirmationDialog"
                              class="text-primary"
                              :disabled="loggedUser.verified_email"
                              cy-data="profile-verify-email-btn"
                            >
                              <v-icon class="mr-2">edit</v-icon>
                              Verify email
                            </v-btn>
                          </div>
                          <div>
                            <v-btn
                              @click="confirmDeleteUser"
                              class="white--text"
                              variant="flat"
                              color="red"
                              cy-data="profile-close-account-btn"
                            >
                              <v-icon class="mr-2">remove_circle</v-icon>
                              Close my account
                            </v-btn>
                          </div>
                        </div>
                      </v-col>
                    </v-row>
                  </v-layout>
                </div>
                <v-divider />
              </v-card-text>
              <slot name="additionalContent"></slot>
            </v-card>
          </v-col>
        </v-row>
      </v-container>
    </v-layout>
  </page-view>
</template>

<script lang="ts">
import { mapState, mapActions } from 'pinia'
import { defineComponent } from 'vue'

import AppContainer from '@/common/components/AppContainer.vue'
import AppSection from '@/common/components/AppSection.vue'
import AppSectionBanner from '@/common/components/AppSectionBanner.vue'
import { ConfirmDialog, useDialogStore } from '@/modules'
import PageView from '@/modules/layout/components/PageView.vue'
import { useLayoutStore } from '@/modules/layout/store'
import ChangePasswordForm from '@/modules/user/components/ChangePasswordForm.vue'
import EditProfileForm from '@/modules/user/components/EditProfileForm.vue'
import { useUserStore } from '@/modules/user/store'

export default defineComponent({
  name: 'ProfileViewTemplate',
  props: {
    name: String
  },
  components: { PageView, AppContainer, AppSection, AppSectionBanner },
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
    showConfirmationDialog(_email) {
      const props = {
        text: 'Do you want send confirmation email?',
        confirmText: 'Send email'
      }
      const listeners = {
        confirm: () => this.resendConfirmationEmail()
      }
      this.show({
        component: ConfirmDialog,
        params: {
          props,
          listeners,
          dialog: { maxWidth: 500, persistent: true }
        }
      })
    },
    confirmDeleteUser() {
      const props = {
        text: 'Are you sure to close your account? <br>  <br> Type in username to confirm:',
        confirmText: 'Submit',
        confirmField: {
          label: 'Username',
          expected: this.loggedUser?.username
        }
      }
      const listeners = {
        confirm: async () => await this.closeUserProfile()
      }
      this.show({
        component: ConfirmDialog,
        params: {
          props,
          listeners,
          dialog: { maxWidth: 500 }
        }
      })
    },
    changePasswordDialog() {
      const props = {}
      const dialog = { maxWidth: 500, persistent: true }
      this.show({
        component: ChangePasswordForm,
        params: {
          props,
          dialog
        }
      })
    },
    editProfileDialog() {
      const props = { profile: this.loggedUser }
      const dialog = { maxWidth: 500, persistent: true }
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
