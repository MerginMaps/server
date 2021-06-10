# Copyright (C) 2018 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

<template>
    <v-card class="layout column main-content fill-height" flat>
      <v-card-title>
        <h2 class="primary--text"> Organisations </h2>
        <v-spacer/>
        <v-card-actions>
          <v-layout align-center shrink>
            <v-text-field
              class="search"
              placeholder="Find organisation"
              append-icon="search"
              v-model="searchFilter"
              hide-details
            />
            <div>
              <v-btn
                @click="createOrganisationDialog"
                outlined
                icon
                color="primary"
              >
                <v-icon >add</v-icon>
              </v-btn>
            </div>
          </v-layout>
        </v-card-actions>
      </v-card-title>

      <v-card-text>
        <v-divider/>
        <br>
        <organisations-table ref="organisationsTable"/>
      </v-card-text>

      <v-card text class="table" flat>
        <v-card-title>
          <h3>Pending Invitations</h3>
        </v-card-title>
        <v-card-text>
          <invitations-table :username="app.user.username" />
        </v-card-text>
      </v-card>

    </v-card>
</template>

<script>
import OrganisationsTable from '@/components/OrganisationsTable'
import InvitationsTable from '@/components/InvitationsTable'
import OrganisationForm from '@/organisation/components/OrganisationForm'
import OrganisationMixin from '@/mixins/Organisation'
import { mapState } from 'vuex'

export default {
  name: 'organisations',
  mixins: [OrganisationMixin],
  components: { OrganisationsTable, InvitationsTable },
  data () {
    return {
      searchFilter: ''
    }
  },
  computed: {
    ...mapState(['app'])
  },
  watch: {
    searchFilter: function () {
      this.$refs.organisationsTable.searchFilter = this.searchFilter
    }
  },
  methods: {
    confirmDeleteOrgs () {
      const props = {
        text: 'Are you sure to delete selected organisations with their projects?',
        confirmText: 'Delete'
      }
      const listeners = {
        confirm: () => this.$refs.organisationsTable.removeSelected()
      }
      this.$dialog.prompt({ props, listeners, dialog: { maxWidth: 500 } })
    },
    createOrganisationDialog () {
      const props = { organisation: {} }
      const dialog = { maxWidth: 500, persistent: true }
      const listeners = {
        success: () => setTimeout(() => { this.getUserOrganisations() }, 1000)
      }
      this.$dialog.show(OrganisationForm, { props, listeners, dialog })
    }
  }
}
</script>

<style lang="scss" scoped>
.v-card.table {
  min-height: unset;
  overflow: unset;
  margin-top: 0px;
}
.v-data-table {
  td {
    text-align: left;
  }
  a {
    text-decoration: none;
  }
  .v-chip {
    ::v-deep .v-chip__content {
      cursor: pointer;
    }
  }
}
.v-input {
  padding-top: 0!important;
  width: 150px;
}
</style>
