<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <v-card>
    <v-card-title>
      <span class="text-h5 text-primary font-weight-bold"
        >Share project {{ project.name }}</span
      >
    </v-card-title>
    <v-card-text>
      <v-layout mt-2 column>
        <h4 class="text-primary">
          {{
            readonly
              ? `Project ${project.name} will be shared with following people`
              : 'Share with'
          }}
        </h4>
        <v-layout v-if="readonly" mx-0 mb-2 row align-center>
          <v-chip-group active-class="text-primary" column>
            <user-search-chip
              v-for="user in addedUsers.slice(0, 5)"
              :item="user"
              :key="user.id"
            />
          </v-chip-group>
          <h4 class="text-primary" v-if="addedUsers && addedUsers.length > 5">
            and {{ addedUsers.length - 5 }} more ...
          </h4>
        </v-layout>
        <v-layout v-else mb-10 column>
          <account-autocomplete
            :inputUsers="addedUsers"
            :filterUsers="projectUsers"
            @update="onAutocompleteUpdate"
            :allowInvite="allowInvite"
          />
          <span class="mt-2" v-if="invitedEmails.length > 0"
            >You will add new people to your workspace in the next step</span
          >
        </v-layout>
      </v-layout>
    </v-card-text>
    <v-card-actions class="flex-row flex flex-wrap">
      <permission-info />
      <v-spacer />
      <div class="flex-row">
        <v-btn @click="closeDialog" variant="outlined">{{
          readonly ? 'Back' : 'Cancel'
        }}</v-btn>
        <v-btn
          id="share-project-btn"
          class="primary"
          :disabled="
            isPending ||
            !addedUsers ||
            addedUsers.length === 0 ||
            !isProjectOwner
          "
          @click="onShare"
        >
          {{ invitedEmails.length === 0 || readonly ? 'Share' : 'Next' }}
        </v-btn>
      </div>
    </v-card-actions>
  </v-card>
</template>

<script lang="ts">
import isEqual from 'lodash/isEqual'
import omit from 'lodash/omit'
import { mapActions, mapState } from 'pinia'
import { PropType, defineComponent } from 'vue'

import AccountAutocomplete from './AccountAutocomplete.vue'
import PermissionInfo from './PermissionInfo.vue'

import { getErrorMessage } from '@/common/error_utils'
import { useDialogStore } from '@/modules/dialog/store'
import { useNotificationStore } from '@/modules/notification/store'
import { useProjectStore } from '@/modules/project/store'
import UserSearchChip from '@/modules/user/components/UserSearchChip.vue'
import { UserSearch, UserSearchInvite } from '@/modules/user/types'

interface Data {
  addedUsers: Array<UserSearchInvite | UserSearch>
  isPending: boolean
}

export default defineComponent({
  name: 'ProjectShareDialog',
  components: { PermissionInfo, UserSearchChip, AccountAutocomplete },
  props: {
    allowInvite: Boolean,
    inputUsers: Array as PropType<Data['addedUsers']>,
    readonly: Boolean,
    name: String
  },
  data(): Data {
    return {
      addedUsers: [],
      isPending: false
    }
  },
  computed: {
    ...mapState(useProjectStore, [
      'currentNamespace',
      'project',
      'isProjectOwner'
    ]),

    projectAccess() {
      return this.project?.access
    },
    projectUsers() {
      return [
        ...this.projectAccess.readersnames,
        ...this.projectAccess.writersnames,
        ...this.projectAccess.ownersnames
      ]
    },
    invitedEmails(): UserSearchInvite[] {
      return this.addedUsers
        ? this.addedUsers.filter((addedUserItem) => addedUserItem.isInvite)
        : []
    }
  },

  created() {
    this.addedUsers = this.inputUsers ?? []
  },

  methods: {
    ...mapActions(useDialogStore, ['close']),
    ...mapActions(useProjectStore, ['saveProjectSettings']),
    ...mapActions(useNotificationStore, ['error']),

    onAutocompleteUpdate(event) {
      this.addedUsers = event
    },

    getNewProjectAccess: function () {
      const addedUsers = this.addedUsers
        .filter((addedUserItem) => !addedUserItem.isInvite)
        .map((addedUserItem) => omit(addedUserItem, ['isInvite']))
      const addedUserNames = addedUsers.map((addedUser) => addedUser.username)
      return {
        access: {
          ...this.projectAccess,
          readersnames: this.projectAccess.readersnames.concat(addedUserNames)
        }
      }
    },

    hasAccessChanged(newAccess, oldAccess) {
      return !isEqual(oldAccess.readersnames, newAccess.readersnames)
    },

    async onShare() {
      if (this.addedUsers && this.addedUsers.length > 0) {
        if (this.allowInvite && this.invitedEmails.length > 0) {
          if (this.readonly) {
            const newProjectAccess = this.getNewProjectAccess()
            this.$emit(
              'on-share',
              newProjectAccess,
              this.hasAccessChanged(newProjectAccess.access, this.projectAccess)
            )
          } else {
            this.$emit(
              'on-invite',
              this.invitedEmails.map((item) => item.email),
              this.addedUsers
            )
          }
          this.isPending = true
        } else {
          const newProjectAccess = this.getNewProjectAccess()
          if (
            this.hasAccessChanged(newProjectAccess.access, this.projectAccess)
          ) {
            try {
              // save only if access has changed
              await this.saveProjectSettings({
                namespace: this.currentNamespace,
                newSettings: newProjectAccess,
                projectName: this.project.name
              })
              this.close()
            } catch (err) {
              this.error({
                text: getErrorMessage(err, 'Failed to save project settings')
              })
            }
          }
          this.addedUsers = []
        }
      }
    },
    closeDialog() {
      if (this.readonly) {
        this.$emit(
          'cancel',
          this.invitedEmails.map((item) => item.email),
          this.addedUsers
        )
      } else {
        this.close()
      }
    }
  }
})
</script>
