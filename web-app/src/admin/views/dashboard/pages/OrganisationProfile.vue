# Copyright (C) 2020 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

<template>
  <page-view :style="`padding-left: ${drawer ? 260 : 20}px; overflow-y: auto; padding-right:20px; margin-right: 0px;`">
    <v-card class="layout column main-content fill-height" flat>
      <v-card-text>
        <div class="profile">
          <h1 class="primary--text"> Profile </h1>
          <br>
          <v-divider/>
          <v-layout>
            <!-- Render profile -->
            <div class="section">
              <ul v-if="organisation">
                <li> <b> Name: </b>{{ organisation.name }} </li>
                <li> <b> Account active: </b>
                  <v-icon v-if="organisation.active" color="green">check</v-icon>
                  <v-icon v-else color="red">clear</v-icon>
                </li>
                <li> <b> Description: </b>{{ organisation.description }} </li>
                <li> <b> Contact Email: </b>{{ organisation.account.email }} </li>
                <br>
                <li> <b> Data Usage: </b>
                 <template v-if="organisation.disk_usage !== undefined && organisation.storage !== undefined">
                   {{ organisation.disk_usage | filesize }} / {{ organisation.storage | filesize }}
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
                <li> <b> Registered: </b>{{ organisation.registration_date | date }} </li>
              </ul>
            </div>
            <v-spacer/>
            <!-- actions -->
            <div v-if="organisation">
              <div>
                <v-tooltip top>
                    <template v-slot:activator="{ on }">
                      <span v-on="on">
                        <v-btn
                          @click="changeStatusDialog"
                          class="primary--text" >
                        <v-icon class="mr-2">edit</v-icon>
                        {{organisation.active ? 'deactivate account' : 'activate account'}}
                        </v-btn>
                      </span>
                    </template>
                    <span v-if="organisation.active">Deactivate account</span>
                    <span v-else >Activate account</span>
                  </v-tooltip>
              </div>
              <div>
                <v-tooltip top >
                    <template v-slot:activator="{ on }">
                      <span v-on="on">
                        <v-btn
                          @click="confirmDeleteAccount"
                          class="white--text"
                          depressed
                          color="red"
                          v-if="organisation.active" >
                          <v-icon class="mr-2">remove_circle</v-icon>
                          close account
                        </v-btn>
                      </span>
                    </template>
                    <span v-if="organisation.active">Delete account</span>
                  </v-tooltip>
              </div>
            </div>
          </v-layout>
          <account-detail :key="name" v-if="organisation"  type="organisation"></account-detail>
        </div>
        <v-divider/>
        <br>
        <h2>Members</h2>
        <organisation-permissions v-if="organisation" :name="organisation.name"></organisation-permissions>
        </v-card-text>
    </v-card>
  </page-view>
</template>

<script>
import { mapState } from 'vuex'
import OrganisationMixin from '@/mixins/Organisation'
import PageView from '@/views/PageView'
import MerginAPIMixin from '@/mixins/MerginAPI'
import OrganisationPermissions from '../components/OrganisationPermissions'
import ConfirmDialog from '@/components/ConfirmDialog'
import CommonMixin from '../../../mixins/CommonAPI'
import { waitCursor } from '@/util'
import AccountDetail from '../components/AccountDetail'

export default {
  name: 'AdminOrganisationView',
  mixins: [OrganisationMixin, MerginAPIMixin, CommonMixin],
  components: { OrganisationPermissions, PageView, AccountDetail },
  props: { name: String },
  computed: {
    ...mapState(['organisation', 'drawer']),
    usage () {
      if (this.organisation) {
        return (this.organisation.storage) ? this.organisation.disk_usage / this.organisation.storage : 0
      }
      return null
    }
  },
  methods: {
    changeStatusDialog () {
      const props = { text: this.organisation.active ? 'Do you really want deactivate this account?' : 'Do you really want activate this account?' }
      const dialog = { maxWidth: 500, persistent: true }
      const listeners = {
        confirm: async () => {
          waitCursor(true)
          await this.changeAccountStatus(this.organisation.account.id, !this.organisation.active)
          await this.getOrganisation(this.name)
          waitCursor(false)
        }
      }
      this.$dialog.show(ConfirmDialog, { props, listeners, dialog })
    },
    confirmDeleteAccount () {
      const props = {
        text: 'Are you sure to close account? All projects will be removed <br>  <br> Type in organisation name to confirm:',
        confirmText: 'Delete',
        confirmField: {
          label: 'Organisation name',
          expected: this.organisation.name
        }
      }
      const listeners = {
        confirm: () => this.closeAccount(this.organisation.account.id)
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
