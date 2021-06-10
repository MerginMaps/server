# Copyright (C) 2018 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

<template>
    <div>
      <v-data-table
        :headers="headers"
        :items="changesets"
        no-data-text="No changeset"
        color="primary"
        footer-props.items-per-page-options='[10, 25, {"text": "$vuetify.dataIterator.rowsPerPageAll","value": -1}]'
        :hide-default-footer="changesets.length <= 10"
      >
        <tr
          slot="items"
          slot-scope="{ item }"
        >
          <template v-for="header in headers">
            <td v-bind:key="header.value" v-if="header">{{ item[header['value']]}}</td>
          </template>
        </tr>
      </v-data-table>
    </div>
</template>

<script>

export default {
  props: {
    namespace: String,
    projectName: String,
    version_id: String,
    path: String,
    asAdmin: {
      type: Boolean,
      default: false
    }
  },
  data () {
    return {
      headers: [],
      changesets: []
    }
  },
  created () {
    this.getChangeset()
  },
  methods: {
    getChangeset () {
      this.$http.get(`/v1/resource/changesets/${this.namespace}/${this.projectName}/${this.version_id}?path=${this.path}`)
        .then(resp => {
          if (resp.data.length) {
            this.headers = [
              { text: 'Table', value: 'table' },
              { text: 'type', value: 'type' }
            ]

            // format the data
            const that = this
            const output = []
            resp.data.forEach(function (data) {
              if (data.table === 'gpkg_contents') {
                return
              }
              data.changes.forEach(function (row) {
                const columnIdentifier = 'Column ' + row.column
                data[columnIdentifier] =
                    (row.old ? row.old : 'N/A') + ' -> ' + (row.new ? row.new : 'N/A')
                that.headers[row.column + 2] = { text: columnIdentifier, value: columnIdentifier }
              })
              output.push(data)
            })
            this.changesets = output
          }
        })
        .catch(err => {
          const msg = (err.response) ? err.response.data.detail : 'Failed to display changeset of file'
          this.$notification.error(msg)
        })
    }
  }
}
</script>
