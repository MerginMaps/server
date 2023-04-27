<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <admin-layout>
    <page-view
      :style="`overflow-y: auto; padding-right:20px; margin-right: 0px;`"
    >
      <v-layout class="column main-content fill-height">
        <v-container>
          <v-row>
            <v-col cols="12" class="pa-0">
              <v-card flat>
                <v-card-text>
                  <div class="profile">
                    <h1 class="primary--text">Profile</h1>
                    <br />
                    <v-divider />
                    <v-layout>
                      <!-- Render profile -->
                      <div class="section">
                        <ul v-if="profile">
                          <li>
                            <b> Username: </b>{{ userAdminProfile.username }}
                          </li>
                          <li><b> Name: </b>{{ profile.first_name }}</li>
                          <li><b> Last name: </b>{{ profile.last_name }}</li>
                          <li>
                            <b> Account active: </b>
                            <v-icon v-if="userAdminProfile.active" color="green"
                              >check
                            </v-icon>
                            <v-icon v-else color="red">clear</v-icon>
                          </li>
                          <li>
                            <b> Email: </b>{{ userAdminProfile.email }}
                            <v-tooltip top>
                              <template v-slot:activator="{ on }">
                                <span v-on="on">
                                  <v-icon
                                    v-if="userAdminProfile.verified_email"
                                    color="green"
                                    >check</v-icon
                                  >
                                  <v-icon v-else color="red">clear</v-icon>
                                </span>
                              </template>
                              <span>Email verification status</span>
                            </v-tooltip>
                          </li>
                          <li>
                            <b> Receive notifications: </b>
                            <v-icon
                              v-if="profile.receive_notifications"
                              color="green"
                              >check
                            </v-icon>
                            <v-icon v-else color="red">clear</v-icon>
                          </li>
                          <li>
                            <b> Registered: </b
                            >{{ $filters.date(profile.registration_date) }}
                          </li>
                        </ul>
                      </div>
                      <v-spacer />
                      <!-- actions -->
                      <div v-if="profile">
                        <div>
                          <v-tooltip top>
                            <template v-slot:activator="{ on }">
                              <span v-on="on">
                                <v-btn
                                  @click="changeStatusDialog"
                                  class="primary--text"
                                >
                                  <v-icon class="mr-2">edit</v-icon>
                                  {{
                                    userAdminProfile.active
                                      ? 'deactivate account'
                                      : 'activate account'
                                  }}
                                </v-btn>
                              </span>
                            </template>
                            <span v-if="userAdminProfile.active"
                              >Deactivate account</span
                            >
                            <span v-else>Activate account</span>
                          </v-tooltip>
                        </div>
                        <div>
                          <v-tooltip top>
                            <template v-slot:activator="{ on }">
                              <span v-on="on">
                                <v-btn
                                  @click="confirmDeleteUser"
                                  class="white--text"
                                  depressed
                                  color="red"
                                >
                                  <v-icon class="mr-2">remove_circle</v-icon>
                                  close account
                                </v-btn>
                              </span>
                            </template>
                            <span>Delete account</span>
                          </v-tooltip>
                        </div>
                      </div>
                    </v-layout>
                  </div>
                </v-card-text>
              </v-card>
            </v-col>
          </v-row>
        </v-container>
      </v-layout>
    </page-view>
  </admin-layout>
</template>

<script lang="ts">
import { ConfirmDialog, PageView } from '@mergin/lib'
import { defineComponent } from 'vue'
import { mapActions, mapState } from 'vuex'

import AdminLayout from '@/modules/admin/components/AdminLayout.vue'

export default defineComponent({
  name: 'ProfileView',
  components: { PageView, AdminLayout },
  props: {
    username: String
  },
  data() {
    return {
      dialog: false
    }
  },
  computed: {
    ...mapState('adminModule', ['userAdminProfile']),
    usage() {
      return this.profile.disk_usage / this.profile.storage
    },
    profile() {
      if (this.userAdminProfile == null) {
        return null
      } else {
        return this.userAdminProfile.profile
      }
    }
  },
  methods: {
    ...mapActions('adminModule', ['closeAccount', 'updateUser']),
    changeStatusDialog() {
      const props = {
        text: this.userAdminProfile.active
          ? 'Do you really want deactivate this account?'
          : 'Do you really want activate this account?'
      }
      const dialog = { maxWidth: 500, persistent: true }
      const listeners = {
        confirm: async () => {
          await this.updateUser({
            username: this.userAdminProfile.username,
            data: {
              active: !this.userAdminProfile.active
            }
          })
        }
      }
      this.$store.dispatch('dialogModule/show', {
        component: ConfirmDialog,
        params: {
          props,
          listeners,
          dialog
        }
      })
    },
    confirmDeleteUser() {
      const props = {
        text: 'Are you sure to close account? All projects will be removed <br>  <br> Type in username to confirm:',
        confirmText: 'Delete',
        confirmField: {
          label: 'Username',
          expected: this.userAdminProfile.username
        }
      }
      const listeners = {
        confirm: async () =>
          await this.closeAccount({ username: this.userAdminProfile.username })
      }
      this.$store.dispatch('dialogModule/prompt', {
        params: { props, listeners, dialog: { maxWidth: 500 } }
      })
    }
  }
})
</script>

<style lang="scss" scoped>
.main-content {
  overflow: auto;
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
    width: 100%;

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
</style>
