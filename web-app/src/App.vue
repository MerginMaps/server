# Copyright (C) 2018 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

<template>
  <v-app>
    <dialog-windows/>
    <v-layout column fill-height>
      <transition name="fade">
        <router-view name="header"/>
      </transition>
      <transition name="fade">
        <router-view :key="$route.fullPath" name="sidebar"/>
      </transition>
      <v-card v-if="pingData && pingData.maintenance"
              outlined
              class="maintenance_warning">
        <v-card-text>
          <b>The service is currently in read-only mode for maintenance. Upload and update functions are not available at this time. Please try again later.</b>
        </v-card-text>
      </v-card>
      <v-layout
        column fill-height
        class="app-content"
      >
        <transition name="fade">
          <router-view  class="page"/>
        </transition>
      </v-layout>

    </v-layout>
    <upload-progress/>
    <notifications/>
  </v-app>
</template>

<script>
import Notifications from '@/components/Notifications'
import DialogWindows from '@/components/DialogWindows'
import UploadProgress from '@/components/UploadProgress'
import { CustomError } from './util'

export default {
  name: 'app',
  components: { UploadProgress, Notifications, DialogWindows },
  metaInfo () {
    return {
      title: 'Mergin',
      meta: [
        { name: 'description', content: 'Store and track changes to your geo-data. Mergin is a repository of geo-data for collaborative work.' },
        { property: 'og:title', content: 'Store and track changes to your geo-data. Mergin is a repository of geo-data for collaborative work.' },
        { property: 'og:site_name', content: 'Mergin' }
      ]
    }
  },
  data () {
    return {
      pingData: null
    }
  },
  computed: {
    app () {
      return this.$store.state.app
    },
    showLogin () {
      return !this.app.user
    },
    error () {
      return this.$store.state.serverError
    }
  },
  watch: {
    error () {
      if (!this.error) return
      this.$notification.error(this.error)
      this.$store.commit('serverError', null) // reset error so it is displayed just once
    }
  },
  created () {
    this.getPingData()
    this.$http.interceptors.request.use(
      request => {
        if (this.pingData && this.pingData.maintenance && request.method !== 'get' && !request.url.includes('/project/by_names') && !request.url.includes('/auth/login')) {
          // mimic regular response object, server will not be called
          const custError = new CustomError('reason', { data: { detail: 'The service is currently in read-only mode for maintenance. Upload and update functions are not available at this time. Please try again later.' }, status: 503 })
          return Promise.reject(custError)
        }
        return request
      },
      error => {
        return Promise.reject(error)
      }
    )
    this.$http.interceptors.response.use(
      response => response,
      error => {
        if (error.response) {
          const { status } = error.response
          if (status === 401 && this.app.user) {
            this.$store.commit('user', null)
          }
        }
        return Promise.reject(error)
      }
    )
  },
  methods: {
    getPingData () {
      this.$http.get('/ping')
        .then(resp => {
          this.pingData = resp.data
        })
        .catch(() => {
          this.$notification.error('Failed to ping server')
        })
    }
  }
}
</script>

<style lang="scss">
html, body, .v-application {
  height: 100%;
  overflow: hidden!important;
  font-size: 14px;
}
.app-content {
  position: relative;
}
a {
  outline: none;
}

h3 {
  color: #2d4470;
}

.fade-leave-active {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
}
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.25s;
}
.fade-enter, .fade-leave-to {
  opacity: 0;
}
.v-data-table {
  tbody {
    td {
      font-size: 13px
    }
  }
}
.maintenance_warning {
  margin: auto;
  width: 100%;
  background-color: orange !important;
  color: rgba(0,0,0,.87) !important;
  padding-left: 400px;
  text-align: center;
  @media (max-width: 960px) {
    padding-left: 40px;
  }
}

.v-data-table  {
  table {
    thead {
      tr {
        th {
          font-weight: 500;
          font-size: 12px;
        }
      }
    }
  }
}

.v-btn.v-size--default {
  font-size: 14px;
  font-weight: 400;
}

.theme--light.v-data-table {
  margin: .5em 0;
  border: 1px solid #ddd;
  border-radius: 3px;
  padding: .5em;
  background-color: #f9f9f9;
}

.v-card__subtitle, .v-card__text {
  font-size: 13px;
}

.v-btn {
  margin: 6px 8px 6px 8px;
  text-transform: capitalize;
}

.v-list-item--link::before {
  background-color: transparent;
}

.v-list-item--link:hover {
    background: rgba(0,0,0,.04);
}

.v-list-item--active {
  color: #2d4470 !important;
}

.v-list--dense .v-list-item {
    min-height: 20px;
}

.v-list-item.v-list-item__content.v-list-item__title {
    font-weight: 300;
}

.theme--light.v-btn:not(.v-btn--flat):not(.v-btn--text):not(.v-btn--outlined){
    background-color: #f5f5f5;
}

.theme--light.v-btn:not(.v-btn--flat):not(.v-btn--text):not(.v-btn--outlined):hover {
    background-color: #999;
}

.theme--light.v-input:not(.v-input--is-disabled) input, .theme--light.v-input:not(.v-input--is-disabled) textarea {
    color: rgba(0,0,0,.87);
}

.v-table tr {
    color: #555;
}

.v-label::first-letter {
  text-transform: uppercase;
}

.v-label {
  min-width: 50px;
}
</style>

<style lang="scss" scoped>
.layout.fill-height {
  overflow: hidden;
  min-height: 0;
}
</style>
