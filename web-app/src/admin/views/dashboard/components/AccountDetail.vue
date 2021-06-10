# Copyright (C) 2021 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.
<template>
  <div
        style="padding-top: 5px;">
    <v-chip
        @click="changeStorageDialog"
        class="primary--text"
        small
    >
      <v-icon class="mr-2">edit</v-icon>
      change storage
    </v-chip>
  </div>
</template>

<script>
import ChangeStorageDialog from '../components/ChangeStorageDialog'
import CommonAPI from '../../../mixins/CommonAPI'
import OrganisationMixin from '@/mixins/Organisation'
import { mapState } from 'vuex'

export default {
  name: 'AccountDetail',
  mixins: [CommonAPI, OrganisationMixin],
  props: {
    type: String
  },
  computed: {
    ...mapState('admin', ['userAdminProfile']),
    ...mapState(['organisation']),
    account () {
      if (this.type === 'user' && this.userAdminProfile) {
        return this.userAdminProfile.account
      } else if (this.organisation) {
        return this.organisation.account
      }
      return null
    }
  },
  methods: {
    changeStorageDialog () {
      const props = { rawStorage: this.type === 'user' ? this.userAdminProfile.profile.storage : this.organisation.storage, accountId: this.account.id }
      const dialog = { maxWidth: 500, persistent: true }
      const listeners = {
        success: () => this.type === 'user' ? this.fetchUserProfileByName(this.userAdminProfile.username) : this.getOrganisation(this.organisation.name)
      }
      this.$dialog.show(ChangeStorageDialog, { props, listeners, dialog })
    }
  }
}
</script>

<style lang="scss"  scoped>
button {
  padding-left: 10px;
  height: 35px;
  padding-right: 10px;
  width: 100%;
  i {
    font-size: 13px;
  }
}
</style>
