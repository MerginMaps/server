# Copyright (C) 2020 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

<template>
  <v-form ref="form" v-model="valid" class="new-org-form">
  <v-card v-on:keyup.enter="submit">
    <v-card-title>
      <span class="headline">
        <span v-if="!editMode">Create organisation</span>
        <span v-else>Edit organisation</span>
      </span>
    </v-card-title>
    <v-card-text>
      <p
        v-if="errorMsg"
        class="text-xs-center red--text"
        v-text="errorMsg"
      />
        <v-text-field
          label="Organisation name"
          counter
          :rules="rules"
          maxlength="25"
          v-model="editedOrganisation.name"
          :error-messages="errors.name"
          @keyup.enter="submit"
          :disabled="editMode"
          hint="Only alphanumeric and hyphens characters are allowed. <br> Spaces are replaced with hyphens."
          @input="v => updateName(v)"
        >
          <template v-slot:message="{ message }">
            <div v-html="message"></div>
          </template>
        </v-text-field>


        <v-textarea
          label="Description"
          counter
          maxlength="256"
          v-model="editedOrganisation.description"
          :error-messages="errors.description"
          @keyup.enter="submit"
        />

        <v-card-actions>
          <v-spacer/>
          <v-btn
              class="text--primary"
              @click="$dialog.close"
          >
            Close
          </v-btn>
          <v-btn
            :disabled="!valid"
            class="primary white--text"
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
import OrganisationMixin from '../../mixins/Organisation'
import { waitCursor } from '../../util'

export default {
  props: {
    organisation: Object
  },
  mixins: [FormMixin, OrganisationMixin],
  data () {
    return {
      editedOrganisation: Object.assign({}, this.organisation),
      valid: false,
      rules: [
        v => (v !== undefined && !v.startsWith('-') && !v.endsWith('-')) || 'Name cannot start/end with -',
        v => (v !== undefined && (v.length <= 25 && v.length >= 4)) || 'Min 4 characters',
        v => /^[a-z\d\-\s]+$/i.test(v) || 'Name cannot contain invalid characters'
      ]
    }
  },
  computed: {
    editMode () {
      return Boolean(this.organisation.name)
    }
  },
  methods: {
    submit () {
      this.clearErrors()
      let errMessage, promise
      waitCursor(true)
      if (this.editMode) {
        promise = this.updateOrganisation(this.organisation.name, this.editedOrganisation)
        errMessage = 'Failed to update organisation'
      } else {
        promise = this.createOrganisation(this.editedOrganisation)
        errMessage = 'Failed to create organisation'
      }
      Promise.resolve(promise).then(() => {
        this.$dialog.close()
        this.$emit('success')
      }).catch(err => {
        this.handleError(err, errMessage)
      })
      waitCursor(false)
    },
    updateName (value) {
      // replace spaces with hyphens according internal rules
      this.editedOrganisation.name = value.replace(/ /g, '-')
      this.valid = this.$refs.form.validate()
    }
  }
}
</script>
