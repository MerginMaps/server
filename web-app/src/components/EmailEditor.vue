# Copyright (C) 2018 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

<template>
  <v-card>
    <v-card-text>
      <v-text-field
        label="Subject"
        v-model="subject"
        single-line
        hide-details
      />
      <wysiwyg v-model="html" />
    </v-card-text>

    <v-card-actions>
      <v-spacer/>
      <v-btn @click="$dialog.close">Close</v-btn>
      <v-btn
        color="primary"
        @click="sendEmails"
        :disabled="!subject"
      >
        Send
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script>

export default {
  props: {
    users: Array
  },
  data () {
    return {
      subject: ''
    }
  },
  methods: {
    sendEmails () {
      const data = {
        users: this.users,
        subject: this.subject,
        html: ''
      }
      this.$http.post('/app/email_notification', data)
        .then(() => {
          this.$notification.show('Email was successfully sent')
          this.$dialog.close()
        })
        .catch(err => {
          this.handleError(err, 'Failed to send notification email')
        })
    }
  }
}
</script>

<style lang="scss" scoped>
</style>
