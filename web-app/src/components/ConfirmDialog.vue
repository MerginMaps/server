# Copyright (C) 2019 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

<template>
  <v-card>
    <v-card-title class="headline">{{ headline }}</v-card-title>
    <v-card-text v-html="text"/>
    <v-card-actions>
      <v-text-field
        v-if="confirmField"
        autofocus
        :label="confirmField.label"
        v-model="confirmValue"
        style="margin-left: 15px"
      />
      <v-spacer/>
      <v-btn
        text
        @click="$dialog.close"
      >
        {{ cancelText }}
      </v-btn>
      <v-btn
        :disabled="!isConfirmed"
        color="primary"
        @click="confirm"
      >
        {{ confirmText }}
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script>
export default {
  props: {
    text: String,
    confirmField: Object,
    confirmText: {
      type: String,
      default: 'Ok'
    },
    cancelText: {
      type: String,
      default: 'Cancel'
    },
    headline: {
      type: String,
      default: 'Confirm'
    }
  },
  data () {
    return {
      confirmValue: ''
    }
  },
  computed: {
    isConfirmed () {
      return (this.confirmField) ? this.confirmField.expected === this.confirmValue : true
    }
  },
  methods: {
    confirm () {
      this.$dialog.close()
      this.$emit('confirm')
    }
  }
}
</script>
