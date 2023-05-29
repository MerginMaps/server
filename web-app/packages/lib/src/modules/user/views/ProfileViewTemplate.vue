<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
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

import { useDialogStore } from '@/modules'
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
  components: { PageView },
  data() {
    return {
      dialog: false
    }
  },
  computed: {
    ...mapState(useLayoutStore, ['drawer']),
    ...mapState(useUserStore, ['loggedUser']),
    usage() {
      return this.loggedUser?.disk_usage / this.loggedUser?.storage
    }
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
    ...mapActions(useDialogStore, ['prompt', 'show']),
    ...mapActions(useUserStore, {
      fetchUserProfile: 'fetchUserProfile',
      resendConfirmationEmailToUser: 'resendConfirmationEmail',
      closeUserProfile: 'closeUserProfile'
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
      this.prompt({
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
        confirmText: 'Delete',
        confirmField: {
          label: 'Username',
          expected: this.loggedUser?.username
        }
      }
      const listeners = {
        confirm: async () => await this.closeUserProfile()
      }
      this.prompt({
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
    }
  }
})
</script>

<style lang="scss" scoped>

.main-content {
  overflow: unset;
}

.col-5 {
  max-width: 100%;
}

.profile {
  margin-bottom: 20px;

  h2 {
    color: #2d4470;
    margin-bottom: 10px;
  }

  button {
    padding-left: 10px;
    height: 35px;
    padding-right: 10px;
    float: right;
    @media (max-width: 770px) {
      width: 100%;
    }
    @media (min-width: 771px) {
      width: 60%;
    }

    i {
      font-size: 13px;
    }
  }

  .align-center {
    padding-top: 10px;
    padding-bottom: 10px;
    align-items: flex-start;
    padding-right: 10px;
  }

  .section {
    margin-right: 10px;

    ul {
      padding-left: 0;
    }

    li {
      list-style: none;

      b {
        width: 150px;
        display: inline-block;
      }
    }

    .v-icon {
      font-size: 18px;
    }
  }
}

@media (max-width: 480px) {
  .action-button {
    width: 135px;
  }
}

.action-button {
  div {
    display: inline-block;
  }
}
</style>
