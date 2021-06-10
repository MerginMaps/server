# Copyright (C) 2020 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

<template>
  <page-view>
    <v-layout class="layout column main-content fill-height" flat v-if="isMember">
      <warning-message  v-if="isAdmin || isOwner"/>
      <v-card-text>
        <div class="profile">
          <h1 class="primary--text"> Profile </h1>
          <br>
          <v-divider/>
          <v-row>
          <v-col lg="8" md="7" sm="9" cols="12" style="color: rgba(0,0,0,.6);">
            <!-- Render profile -->
            <div class="section">
              <ul v-if="organisation">
                <li> <b> Name: </b>{{ organisation.name }} </li>
                <li> <b> Description: </b>{{ organisation.description }} </li>
                <li> <b> Contact Email: </b>{{ organisation.account.email }} </li>
                <li> <b> Registered: </b>{{ organisation.registration_date | date }} </li>
                <br>
              </ul>
            </div>
            <v-spacer/>
            </v-col>
            <!-- actions -->
            <v-col lg="3" offset-lg="1" md="3" offset-md="1" sm="5" offset-sm="4" cols="5" offset="3">
            <div v-if="isOwner">
              <div>
                <v-btn
                  @click="editOrganisationDialog"
                  class="primary--text"
                >
                <v-icon class="mr-2">edit</v-icon>
                edit profile
                </v-btn>
              </div>
              <div>
                <v-btn
                  @click="confirmDeleteOrganisation"
                  class="white--text"
                  depressed
                  color="red"
                >
                  <v-icon class="mr-2">remove_circle</v-icon>
                  close organisation
                </v-btn>
              </div>
            </div>
          </v-col>
          </v-row>
        </div>
        <v-divider/>
      </v-card-text>
      <v-card class="table" flat
              v-if="isWriter">
        <v-card-text>
      <h3>Project transfers</h3>
      <transfers-table :namespace="organisation.name"/>
        </v-card-text>
        </v-card>
      </v-layout>
  </page-view>
</template>

<script>
import union from 'lodash/union'
import { mapState } from 'vuex'
import OrganisationMixin from '../../mixins/Organisation'
import PageView from '@/views/PageView'
import OrganisationForm from '@/organisation/components/OrganisationForm'
import MerginAPIMixin from '@/mixins/MerginAPI'
import { waitCursor } from '@/util'
import TransfersTable from '@/components/TransfersTable'
import WarningMessage from '@/components/WarningMessage'


export default {
  name: 'organisation-profile',
  mixins: [OrganisationMixin, MerginAPIMixin],
  components: { PageView, TransfersTable, WarningMessage },
  props: { name: String },
  computed: {
    ...mapState(['app', 'organisation']),
    usage () {
      if (this.organisation) {
        return (this.organisation.storage) ? this.organisation.disk_usage / this.organisation.storage : 0
      }
      return null
    },
    isOwner () {
      if (this.organisation && this.app.user) {
        return this.organisation.owners.includes(this.app.user.username)
      }
      return null
    },
    isAdmin () {
      if (this.organisation && this.app.user) {
        return this.isOwner || this.organisation.admins.includes(this.app.user.username)
      }
      return null
    },
    isMember () {
      if (this.organisation && this.app.user) {
        return this.isAdmin || union(this.organisation.writers, this.organisation.readers).includes(this.app.user.username)
      }
      return null
    },
    isWriter () {
      if (this.organisation && this.app.user) {
        return this.isAdmin || this.organisation.writers.includes(this.app.user.username)
      }
      return null
    }
  },
  methods: {
    confirmDeleteOrganisation () {
      const props = {
        text: 'Are you sure to close this organisation? All projects under this organisation will be removed. <br> <br> Type in organisation name to confirm:',
        confirmText: 'Delete',
        confirmField: {
          label: 'Organisation name',
          expected: this.name
        }
      }
      const listeners = {
        confirm: () => {
          this.closeAccount()
        }
      }
      this.$dialog.prompt({ props, listeners, dialog: { maxWidth: 500 } })
    },
    closeAccount () {
      waitCursor(true)
      const promise = this.$http.delete(`/app/account/${this.organisation.account.id}`, { 'axios-retry': { retries: 5 } })
      Promise.resolve(promise).then(() => {
        location.href = '/'
      }).catch(err => {
        const msg = (err.response) ? err.response.data.detail : 'Unable to close account'
        this.$notification.error(msg)
      }).finally(() => { waitCursor(false) })
    },
    editOrganisationDialog () {
      const props = { organisation: this.organisation }
      const dialog = { maxWidth: 500, persistent: true }
      const listeners = {
        success: () => {
          this.getOrganisation(this.name)
          this.$notification.show('Updated successfully')
        }
      }
      this.$dialog.show(OrganisationForm, { props, listeners, dialog })
    }
  }
}
</script>

<style lang="scss" scoped>
.main-content {
  overflow: auto;
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
