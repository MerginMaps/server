# Copyright (C) 2018 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

<template>
  <v-card v-on:keyup.enter="accept()">
    <v-card-title>
      <span class="headline">Accept project transfer</span>
      <span class="note flex-auto-l transfer">
        This will move project to your namespace. You may want to change name and decide whether to keep original project permissions.
      </span>
    </v-card-title>
    <v-card-text>
      <v-text-field
        disabled
        label="Original owner"
        v-model="transfer.from_ns_name"
      />
     <v-text-field
        disabled
        label="Target owner"
        v-model="transfer.to_ns_name"
      >
     </v-text-field>
      <v-text-field
        label="Project name"
        v-model="projectName"
        :error-messages="errors.project"
      />
      <v-checkbox
        label="Keep permissions"
        color="primary"
        v-model="transferPermissions"
      />

    </v-card-text>
    <v-card-actions>
      <v-spacer/>
      <v-btn @click="$dialog.close">
        Close
      </v-btn>
      <v-btn
        class="primary"
        :disabled="!projectName"
        @click="accept"
      >
        Accept transfer
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script>
import FormMixin from '@/mixins/Form'
import MerginAPIMixin from '@/mixins/MerginAPI'

export default {
  mixins: [FormMixin, MerginAPIMixin],
  props: {
    transfer: Object
  },
  data () {
    return {
      projectName: '',
      transferPermissions: true
    }
  },
  created () {
    this.projectName = this.transfer.project_name
  },
  methods: {
    async accept () {
      const props = {
        name: this.projectName,
        transfer_permissions: this.transferPermissions
      }
      const success = await this.acceptTransfer(this.transfer, props)
      if (success) { this.$dialog.close() }
    }
  }
}
</script>
<style lang="scss" scoped>
  .note{
    color: #616161;
    margin-top: 10px;
  }
  .transfer{
    margin-top: 10px;
    display: block;
    font-size: 14px;
  }
  .v-card__title{
    word-break: normal;
  }
  .headline{
    font-size: 24px !important;
  }
</style>
