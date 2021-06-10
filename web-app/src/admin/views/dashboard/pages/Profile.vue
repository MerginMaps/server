# Copyright (C) 2020 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

<template>
    <page-view>
   <v-card class="layout column main-content fill-height" flat>
      <v-card-text>
        <div class="profile">
          <h1 class="primary--text"> Profile </h1>
          <br>
          <v-divider/>
          <v-layout>
            <!-- Render profile -->
            <div class="section">
              <ul v-if="profile">
                <li> <b> Username: </b>{{ userAdminProfile.username }} </li>
                <li> <b> Name: </b>{{ profile.first_name }} </li>
                <li> <b> Last name: </b>{{ profile.last_name }} </li>
                <li> <b> Account active: </b>
                  <v-icon v-if="userAdminProfile.active" color="green">check</v-icon>
                  <v-icon v-else color="red">clear</v-icon>
                </li>
                <li> <b> Email: </b>{{ userAdminProfile.email }}
                  <v-tooltip top >
                    <template v-slot:activator="{ on }">
                    <span
                      v-on="on"
                    >
                      <v-icon v-if="userAdminProfile.verified_email" color="green">check</v-icon>
                      <v-icon v-else color="red">clear</v-icon>
                    </span>
                    </template>
                    <span>Email verification status</span>
                  </v-tooltip>
                </li>
                <li> <b> Receive notifications: </b>
                  <v-icon v-if="profile.receive_notifications" color="green">check</v-icon>
                  <v-icon v-else color="red">clear</v-icon>
                </li>
                <br>
                <li> <b> Data Usage: </b>
                 <template v-if="profile.disk_usage !== undefined && profile.storage !== undefined">
                   {{ profile.disk_usage | filesize }} / {{ profile.storage | filesize }}
                    <v-progress-circular
                      :size="55"
                      :width="8"
                      :value="usage * 100"
                      color="primary"
                      class="mx-3"
                    >
                      {{ Math.floor(usage * 100) }}%
                    </v-progress-circular>
                  </template>
                </li>
                <li> <b> Registered: </b>{{ profile.registration_date | date }} </li>
              </ul>
            </div>
            <v-spacer/>
            <!-- actions -->
            <div v-if="profile">
              <div>
               <v-tooltip top >
                    <template v-slot:activator="{ on }">
                      <span v-on="on">
                        <v-btn
                          @click="changeStatusDialog"
                          class="primary--text" >
                        <v-icon class="mr-2">edit</v-icon>
                        {{userAdminProfile.active ? 'deactivate account' : 'activate account'}}
                        </v-btn>
                      </span>
                    </template>
                    <span v-if="userAdminProfile.active">Deactivate account</span>
                    <span v-else >Activate account</span>
                  </v-tooltip>
              </div>
              <div>
                <v-tooltip top >
                    <template v-slot:activator="{ on }">
                      <span v-on="on">
                        <v-btn
                          @click="confirmDeleteUser"
                          class="white--text"
                          depressed
                          color="red"
                          v-if="userAdminProfile.active" >
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
            <account-detail :key="username" v-if="profile" type="user"></account-detail>
        </div>
        </v-card-text>
    </v-card>
    </page-view>
</template>

<script>
import { mapState } from 'vuex'
import CommonMixin from '../../../mixins/CommonAPI'
import PageView from '@/views/PageView'
import ConfirmDialog from '@/components/ConfirmDialog'
import MerginAPIMixin from '@/mixins/MerginAPI'
import { waitCursor } from '@/util'
import AccountDetail from '../components/AccountDetail'


export default {
  name: 'AdminUserView',
  mixins: [CommonMixin, MerginAPIMixin],
  components: { PageView, AccountDetail },
  props: {
    username: String
  },
  data () {
    return {
      dialog: false
    }
  },
  computed: {
    ...mapState('admin', ['userAdminProfile']),
    usage () {
      return this.profile.disk_usage / this.profile.storage
    },
    profile () {
      if (this.userAdminProfile !== null) {
        return this.userAdminProfile.profile
      } else {
        return null
      }
    }
  },
  methods: {
    changeStatusDialog () {
      const props = { text: this.userAdminProfile.active ? 'Do you really want deactivate this account?' : 'Do you really want activate this account?' }
      const dialog = { maxWidth: 500, persistent: true }
      const listeners = {
        confirm: async () => {
          waitCursor(true)
          await this.changeAccountStatus(this.userAdminProfile.account.id, !this.userAdminProfile.active)
          await this.fetchUserProfileByName(this.username)
          waitCursor(false)
        }
      }
      this.$dialog.show(ConfirmDialog, { props, listeners, dialog })
    },
    confirmDeleteUser () {
      const props = {
        text: 'Are you sure to close account? All projects will be removed <br>  <br> Type in username to confirm:',
        confirmText: 'Delete',
        confirmField: {
          label: 'Username',
          expected: this.userAdminProfile.username
        }
      }
      const listeners = {
        confirm: () => this.closeAccount(this.userAdminProfile.account.id)
      }
      this.$dialog.prompt({ props, listeners, dialog: { maxWidth: 500 } })
    }
  }
}
</script>

<style lang="scss" scoped>
.main-content {
  overflow: auto;
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
    width: 100%;
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
</style>
