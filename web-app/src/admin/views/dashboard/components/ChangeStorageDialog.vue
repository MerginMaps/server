# Copyright (C) 2021 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.
<template>
  <v-form ref="form">
  <v-card v-on:keyup.enter="submit" v-on:keyup.esc="closeIt">
    <v-card-title>
      <span class="headline">
        <span>Change storage</span>
      </span>
    </v-card-title>
    <v-card-text>
      <p
        v-if="errorMsg"
        class="text-xs-center red--text"
        v-text="errorMsg"
      />

      <v-text-field
          autofocus
          type="number"
          label="storage"
          v-model="storage"
          suffix="MB"
          :min="1"
        />

        <v-card-actions>
          <v-spacer/>
          <v-btn class="black--text" @click="$dialog.close">
            Close
          </v-btn>
          <v-btn
            class="orange white--text"
            @click="submit"
          >
            Save
          </v-btn>
        </v-card-actions>
    </v-card-text>
  </v-card>
</v-form>
</template>

<script>
import FormMixin from '@/mixins/Form'
import CommonAPI from '@/admin/mixins/CommonAPI'

export default {
  name: 'ChangeStorageDialog',
  mixins: [FormMixin, CommonAPI],
  props: {
    rawStorage: Number,
    accountId: Number
  },
  data () {
    return {
      storage: null
    }
  },
  created () {
    this.storage = parseInt(this.rawStorage / (1024 * 1024))
  },
  methods: {
    submit () {
      this.clearErrors()
      const storage = this.storage * 1024 * 1024
      const promise = this.updateAccountStorage(this.accountId, storage)
      const errMessage = 'Failed to update account\'s storage'
      Promise.resolve(promise).then(() => {
        this.$dialog.close()
        this.$emit('success')
      }).catch(err => {
        this.handleError(err, errMessage)
      })
    },
    closeIt () {
      this.$dialog.close()
    }
  }
}
</script>

<style scoped>

</style>
