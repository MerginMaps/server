# Copyright (C) 2018 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

<template>
  <v-layout class="column main-content fill-height">
    <v-card  flat>
      <v-card-text>
        <div class="profile">
          <h1 class="primary--text"> Profile </h1>
          <br>
          <v-divider/>
          <v-layout
            align-center>
            <v-row>
              <v-col>
            <!-- Render profile -->
            <div class="section">
              <ul v-if="profile">
                <li><b> Username: </b>{{ profile.username }}</li>
                <li><b> Name: </b>{{ profile.name }}</li>
                <li><b> Email: </b>{{ profile.email }}
                  <v-tooltip top v-if="'project-versions' !== $route.name && 'project-versions-detail' !== $route.name">
                    <template v-slot:activator="{ on }">
                    <span
                        v-on="on"
                    >
                      <v-icon v-if="app.user.verified_email" color="green">check</v-icon>
                      <v-icon v-else color="red">clear</v-icon>
                    </span>
                    </template>
                    <span>Email verification status</span>
                  </v-tooltip>
                </li>
                <li><b> Receive notifications: </b>
                  <v-icon v-if="profile.receive_notifications" color="green">check</v-icon>
                  <v-icon v-else color="red">clear</v-icon>
                </li>
                <li><b> Registered: </b>{{ profile.registration_date | date }}</li>
                <br>
              </ul>
            </div>
            <v-spacer/>
                </v-col>
            <!-- actions -->
              <v-col>
            <div>
              <div>
                <v-btn
                    @click="changePasswordDialog"
                    class="primary--text"
                >
                  <v-icon class="mr-2">edit</v-icon>
                  Change password
                </v-btn>
              </div>
              <div>
                <v-btn
                    @click="editProfileDialog"
                    class="primary--text"
                >
                  <v-icon class="mr-2">edit</v-icon>
                  Edit profile
                </v-btn>
              </div>
              <div>
                <v-btn
                    @click="showConfirmationDialog"
                    class="primary--text"
                    :disabled="app.user.verified_profile"
                >
                  <v-icon class="mr-2">edit</v-icon>
                  Verify email
                </v-btn>
              </div>
              <div>
                <v-btn
                    @click="confirmDeleteUser"
                    class="white--text"
                    depressed
                    color="red"
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
        <v-divider/>
      </v-card-text>
      <v-card class="table" flat>
        <v-card-text>
          <h3>Organisations</h3>
          <organisations-table ref="organisationsTable"/>
        </v-card-text>
      </v-card>
      <v-card class="table" flat>
        <v-card-title>
        </v-card-title>
        <v-card-text>
          <h3>Pending Invitations</h3>
          <invitations-table :username="app.user.username"/>
        </v-card-text>
      </v-card>
    </v-card>
  </v-layout>
</template>

<script>
import { mapState } from 'vuex'
import ChangePasswordForm from '@/user/components/ChangePasswordForm'
import EditProfileForm from '@/user/components/EditProfileForm'
import MerginAPIMixin from '@/mixins/MerginAPI'
import OrganisationsTable from '@/components/OrganisationsTable'
import InvitationsTable from '@/components/InvitationsTable'
import { waitCursor } from '@/util'


export default {
  name: 'profile',
  mixins: [MerginAPIMixin],
  components: { OrganisationsTable, InvitationsTable },
  props: {
    name: String
  },
  data () {
    return {
      dialog: false
    }
  },
  computed: {
    ...mapState(['app', 'users', 'transfers']),
    usage () {
      return this.profile.disk_usage / this.profile.storage
    },
    profile () {
      return this.app.user.profile
    }
  },
  created () {
    this.fetchUserProfile(this.app.user.username)
  },
  watch: {
    name: function () {
      this.fetchUserProfile(this.app.user.username)
    }
  },
  methods: {
    closeUserAccount () {
      waitCursor(true)
      const promise = this.$http.delete(`/app/account/${this.app.user.account.id}`, { 'axios-retry': { retries: 5 } })
      Promise.resolve(promise).then(() => {
        location.href = '/'
      }).catch(err => {
        const msg = (err.response && err.response.data.detail) ? err.response.data.detail : 'Unable to close account'
        this.$notification.error(msg)
      }).finally(() => { waitCursor(false) })
    },
    showConfirmationDialog (email) {
      const props = {
        text: 'Do you want send confirmation email?',
        confirmText: 'Send email'
      }
      const listeners = {
        confirm: () => this.sendConfirmationEmail(this.app.user.email)
      }
      this.$dialog.prompt({ props, listeners, dialog: { maxWidth: 500, persistent: true } })
    },
    confirmDeleteUser () {
      const props = {
        text: 'Are you sure to close your account? All your projects will be removed <br>  <br> Type in username to confirm:',
        confirmText: 'Delete',
        confirmField: {
          label: 'Username',
          expected: this.app.user.username
        }
      }
      const listeners = {
        confirm: () => this.closeUserAccount()
      }
      this.$dialog.prompt({ props, listeners, dialog: { maxWidth: 500 } })
    },
    changePasswordDialog () {
      const props = {}
      const dialog = { maxWidth: 500, persistent: true }
      this.$dialog.show(ChangePasswordForm, { props, dialog })
    },
    editProfileDialog () {
      const props = { profile: this.app.user.profile }
      const dialog = { maxWidth: 500, persistent: true }
      const listeners = {
        success: () => { this.fetchUserProfile(this.app.user.username) }
      }
      this.$dialog.show(EditProfileForm, { props, listeners, dialog })
    }
  }
}
</script>

<style lang="scss" scoped>
.main-content {
  overflow: unset;
}
.col-5 {
  max-width: 100%;
}
.profile{
  margin-bottom: 20px;
  h2 {
    color: #2D4470;
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
      width: 50%;
    }
    i {
      font-size: 13px;
    }
  }
  .align-center{
    padding-top: 10px;
    padding-bottom: 10px;
    align-items: flex-start;
    padding-right: 10px;
  }
  .section{
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

@media (max-width : 480px) {
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
